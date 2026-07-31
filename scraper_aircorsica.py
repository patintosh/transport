import os
import sqlite3
import csv
import subprocess
from datetime import datetime, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE = "https://book.aircorsica.com/plnext/AirCorsicaDX"
CSV_FILENAME = "air_corsica_flights.csv"

def load_chrome_cookies(profile_path):
    """Extrait les cookies du profil Chrome local (SQLite) si disponible"""
    cookies_file = os.path.join(profile_path, "Default", "Network", "Cookies")
    if not os.path.exists(cookies_file):
        cookies_file = os.path.join(profile_path, "Default", "Cookies")
    
    cookies = {}
    if not os.path.exists(cookies_file):
        return cookies

    try:
        temp_db = "cookies_temp.db"
        with open(cookies_file, "rb") as src, open(temp_db, "wb") as dst:
            dst.write(src.read())

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM cookies")
        for row in cursor.fetchall():
            cookies[row[0]] = row[1]
        
        conn.close()
        os.remove(temp_db)
    except Exception as e:
        print(f"Erreur lors de la lecture des cookies : {e}")

    return cookies

def create_session():
    """Crée une session curl_cffi imitant Chrome et initialise le parcours"""
    profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    cookies = load_chrome_cookies(profile_path)

    print(f"Nombre de cookies chargés : {len(cookies)}")

    s = requests.Session(impersonate="chrome")
    if cookies:
        s.cookies.update(cookies)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": BASE + "/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Connection": "keep-alive"
    }

    init_url = f"{BASE}/Preload.action?LANGUAGE=FR&SITE=BDEQBNEW"
    r = s.get(init_url, headers=headers)
    print(f"Statut d'initialisation (Preload) : {r.status_code}")

    return s

def fetch_flight_data(session):
    """Récupère et parse les données de vol réelles (J+7)"""
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"Recherche des vols pour la date : {target_date}")

    search_url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action"
    params = {
        "DATE": target_date,
        "LANGUAGE": "FR",
        "SITE": "BDEQBNEW"
    }

    r = session.get(search_url, params=params)
    print(f"Statut de la requête de vol : {r.status_code}")
    
    flights = []
    if r.status_code == 200:
        if "Pardon Our Interruption" in r.text or "Access Denied" in r.text:
            print("Attention : La page renvoyée est une page de blocage Imperva.")
            return flights

        soup = BeautifulSoup(r.text, "html.parser")
        flight_elements = soup.find_all("div", class_="flight-row")
        
        if flight_elements:
            for elem in flight_elements:
                route = elem.find("span", class_="route").text.strip() if elem.find("span", class_="route") else "AJA-ORY"
                price = elem.find("span", class_="price").text.strip() if elem.find("span", class_="price") else "N/A"
                flights.append({"Date": target_date, "Route": route, "Price": price})
        else:
            print("Structure HTML reçue, aucun élément ciblé trouvé avec les sélecteurs actuels. Sauvegarde d'un log de contrôle.")
            flights.append({"Date": target_date, "Route": "DISPONIBLE", "Price": "CHECK_HTML"})

    return flights

def save_to_csv(data):
    """Enregistre les données dans le CSV sans colonne TIME"""
    file_exists = os.path.exists(CSV_FILENAME)
    
    with open(CSV_FILENAME, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Route", "Price"])
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)
    print("Données enregistrées dans le CSV.")

def git_commit_and_push():
    """Automatise le commit et le push Git des résultats"""
    try:
        subprocess.run(["git", "add", CSV_FILENAME], check=True)
        subprocess.run(["git", "commit", "-m", f"Automated scrape update: {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Modifications poussées avec succès sur le dépôt Git.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'opération Git : {e}")

if __name__ == "__main__":
    session = create_session()
    flights = fetch_flight_data(session)
    if flights:
        save_to_csv(flights)
        git_commit_and_push()