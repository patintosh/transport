import requests
import time
import json
from statistics import mean
import datetime
import csv
import os
import smtplib
from email.message import EmailMessage
import sqlite3

BASE = "https://book.aircorsica.com/plnext/AirCorsicaDX"

# ============================================================
# 0. Charger les cookies Imperva depuis chrome_profile
# ============================================================

def load_chrome_cookies(profile_path):
    cookies_db = os.path.join(profile_path, "Default", "Cookies")

    if not os.path.exists(cookies_db):
        raise Exception(f"Cookies DB introuvable : {cookies_db}")

    conn = sqlite3.connect(cookies_db)
    cursor = conn.cursor()

    cursor.execute("SELECT host_key, name, value FROM cookies")
    cookies = cursor.fetchall()

    conn.close()

    jar = requests.cookies.RequestsCookieJar()
    for host, name, value in cookies:
        if "aircorsica" in host.lower() or "incap" in name.lower():
            jar.set(name, value, domain=host)

    return jar


# ============================================================
# 1. Alerte email (SMTP Apple iCloud)
# ============================================================

def send_email_alert(subject, body):
    smtp_host = "smtp.mail.me.com"
    smtp_port = 587
    smtp_user = "patrice.salini@me.com"
    smtp_pass = os.getenv("ICLOUD_APP_PASSWORD")
    to_email = "patrice.salini@me.com"

    if smtp_pass is None:
        print("⚠ Aucun mot de passe SMTP iCloud trouvé (ICLOUD_APP_PASSWORD). Alerte non envoyée.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print("Alerte email envoyée.")
    except Exception as e:
        print(f"Erreur envoi email : {e}")


# ============================================================
# 2. Session + cookies Imperva
# ============================================================

def create_session():
    profile_path = os.path.join(os.getcwd(), "chrome_profile")
    cookies = load_chrome_cookies(profile_path)

    s = requests.Session()
    s.cookies.update(cookies)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "*/*",
        "Referer": BASE + "/"
    }

    r = s.get(BASE + "/", headers=headers)

    if not any("incap" in c.lower() for c in s.cookies.keys()):
        raise Exception("Imperva n'a pas délivré de cookie. Impossible de scraper.")

    return s


# ============================================================
# 3. Récupération des routes réelles d'Air Corsica
# ============================================================

def get_routes(session):
    return [
        ("ORY", "AJA"),
        ("ORY", "BIA"),
        ("ORY", "CLY"),
        ("ORY", "FSC")
    ]


# ============================================================
# 4. Appel FlexPricer (avec diagnostic d'erreur)
# ============================================================

def flex_pricer(session, origin, dest, date_str):
    jsessionid = session.cookies.get("JSESSIONID")
    url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action;jsessionid={jsessionid}"

    payload = {
        "COUNTRY_SITE": "GB",
        "DATE_RANGE_QUALIFIER_2": "C",
        "BOOKING_FLOW": "REVENUE",
        "INITIAL_TRIP_TYPE": "O",
        "DATE_RANGE_QUALIFIER_1": "C",
        "PAGE_TICKET": "1",
        "STATE": "REGULAR",
        "B_ANY_TIME_1": "TRUE",
        "B_ANY_TIME_2": "TRUE",
        "TRIP_FLOW": "YES",
        "DISPLAY_TYPE": "1",
        "LANGUAGE": "FR",
        "ARRANGE_BY": "D",
        "COMMERCIAL_FARE_FAMILY_1": "CFFYJV1",
        "SITE": "BDEQBNEW",
        "isOverrideAction": "false",
        "PLTG_IS_UPSELL": "true",
        "E_LOCATION_1": dest,
        "E_LOCATION_2": origin,
        "_t": int(time.time()),
        "TRIP_TYPE": "O",
        "PRICING_TYPE": "O",
        "OFFICE_ID": "AJAXK08AB",
        "HAS_INFANT_1": "FALSE",
        "FORCE_CALENDAR": "FALSE",
        "DATE_RANGE_VALUE_1": "0",
        "DATE_RANGE_VALUE_2": "0",
        "B_DATE_1": date_str,
        "B_DATE_2": date_str,
        "TRAVELLER_TYPE_1": "ADT",
        "DATA_TYPE": "json"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "*/*",
        "Referer": BASE + "/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    }

    r = session.post(url, data=payload, headers=headers)

    if "html" in r.text.lower() or not r.text.strip():
        print(f"⚠ Échec route {origin} → {dest} (Statut: {r.status_code}) - Réponse rejetée ou bloquée par Imperva.")
        print(f"Extrait réponse : {r.text[:200]}")
        return {}

    try:
        return r.json()
    except Exception as e:
        print(f"⚠ Erreur JSON pour {origin} → {dest} : {e}")
        print(f"Extrait réponse : {r.text[:200]}")
        return {}


# ============================================================
# 5. Extraction des prix (avec diagnostic de structure JSON)
# ============================================================

def extract_prices(data):
    try:
        price_list = data["priceByBound"][0]["priceList"]
        return [p["amount"] + 3.0 for p in price_list if "amount" in p]
    except Exception as e:
        print(f"⚠ Structure JSON inattendue : {e}")
        print(f"Clés reçues dans le JSON : {list(data.keys()) if isinstance(data, dict) else 'Pas un dictionnaire'}")
        return []


# ============================================================
# 6. Statistiques min / max / moyenne
# ============================================================

def compute_stats(prices):
    if not prices:
        return None
    return {
        "min": min(prices),
        "max": max(prices),
        "mean": mean(prices)
    }


# ============================================================
# 7. Append global CSV
# ============================================================

def append_to_global_csv(rows, filename="résultats_aircorsica.csv"):
    existing = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    all_rows = existing + rows

    all_rows_sorted = sorted(
        all_rows,
        key=lambda r: (r["scrape_date"], r["flight_date"], r["origin"], r["dest"])
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scrape_date", "flight_date", "origin", "dest", "min", "max", "mean"]
        )
        writer.writeheader()
        writer.writerows(all_rows_sorted)


# ============================================================
# 8. Append route CSV
# ============================================================

def append_to_route_csv(rows, origin, dest):
    os.makedirs("routes_aircorsica", exist_ok=True)
    filename = f"routes_aircorsica/{origin}_{dest}.csv"

    existing = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    all_rows = existing + rows

    all_rows_sorted = sorted(
        all_rows,
        key=lambda r: (r["scrape_date"], r["flight_date"])
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scrape_date", "flight_date", "min", "max", "mean"]
        )
        writer.writeheader()
        writer.writerows(all_rows_sorted)


# ============================================================
# 9. Main
# ============================================================

if __name__ == "__main__":
    session = create_session()

    scrape_date = datetime.datetime.now().strftime("%Y%m%d")
    flight_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y%m%d0000")

    global_rows = []

    routes = get_routes(session)

    for origin, dest in routes:
        data = flex_pricer(session, origin, dest, flight_date)
        prices = extract_prices(data)
        stats = compute_stats(prices)

        if stats:
            row = {
                "scrape_date": scrape_date,
                "flight_date": flight_date,
                "origin": origin,
                "dest": dest,
                "min": stats["min"],
                "max": stats["max"],
                "mean": stats["mean"]
            }

            global_rows.append(row)
            append_to_route_csv([row], origin, dest)

            if row["mean"] > 300:
                send_email_alert(
                    subject=f"Alerte prix élevé {origin} → {dest}",
                    body=f"Prix moyen = {row['mean']} € pour le vol du {row['flight_date']}."
                )

    append_to_global_csv(global_rows)

    print(f"{len(global_rows)} lignes ajoutées à résultats_aircorsica.csv")