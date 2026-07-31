import os
import sys
import csv
import subprocess
from datetime import datetime, timedelta

# Vérification et importation sécurisée des dépendances
try:
    from curl_cffi import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    with open("scraper.log", "w", encoding="utf-8") as f:
        f.write(f"ERREUR CRITIQUE : Dépendance manquante - {e}\n")
    sys.exit(1)

BASE = "https://book.aircorsica.com/plnext/AirCorsicaDX"
CSV_FILENAME = "air_corsica_flights.csv"
LOG_FILENAME = "scraper.log"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    with open(LOG_FILENAME, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")

def create_session():
    s = requests.Session(impersonate="chrome")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Connection": "keep-alive"
    }
    s.headers.update(headers)

    init_url = f"{BASE}/Preload.action?LANGUAGE=FR&SITE=BDEQBNEW"
    r = s.get(init_url)
    log_message(f"Statut d'initialisation (Preload) : {r.status_code}")
    log_message(f"Cookies capturés après Preload : {dict(s.cookies)}")

    return s

def fetch_flight_data(session):
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    log_message(f"Recherche des vols pour la date : {target_date}")

    search_url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action"
    params = {
        "DATE": target_date,
        "LANGUAGE": "FR",
        "SITE": "BDEQBNEW"
    }

    session.headers.update({"Referer": f"{BASE}/Preload.action?LANGUAGE=FR&SITE=BDEQBNEW"})

    r = session.get(search_url, params=params)
    log_message(f"Statut de la requête de vol : {r.status_code}")
    
    flights = []
    if r.status_code == 200:
        if "Pardon Our Interruption" in r.text or "Access Denied" in r.text or "captcha" in r.text.lower():
            log_message("ALERTE : La page renvoyée est une page de blocage Imperva.")
            with open("imperva_debug.html", "w", encoding="utf-8") as f:
                f.write(r.text)
            
            # Analyse rapide du contenu bloqué pour le log
            if "reese84" in r.text or "_Incapsula_Resource" in r.text:
                log_message("Type de défi détecté : Script de challenge JS Imperva (reese84).")
            elif "captcha" in r.text.lower():
                log_message("Type de défi détecté : CAPTCHA bloquant.")
            else:
                log_message("Type de défi détecté : Blocage standard ou personnalisé.")

            return flights

        soup = BeautifulSoup(r.text, "html.parser")
        flight_elements = soup.find_all("div", class_="flight-row")
        
        if flight_elements:
            for elem in flight_elements:
                route = elem.find("span", class_="route").text.strip() if elem.find("span", class_="route") else "AJA-ORY"
                price = elem.find("span", class_="price").text.strip() if elem.find("span", class_="price") else "N/A"
                flights.append({"Date": target_date, "Route": route, "Price": price})
        else:
            log_message("Structure HTML reçue, aucun élément ciblé trouvé avec les sélecteurs actuels.")
            flights.append({"Date": target_date, "Route": "DISPONIBLE", "Price": "CHECK_HTML"})

    return flights

def save_to_csv(data):
    file_exists = os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Route", "Price"])
        if not file_exists:
            writer.writeheader()
        for row in data:
            writer.writerow(row)
    log_message("Données enregistrées dans le CSV.")

def git_commit_and_push():
    try:
        subprocess.run(["git", "add", CSV_FILENAME], check=True)
        subprocess.run(["git", "commit", "-m", f"Automated scrape update: {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        log_message("Modifications poussées avec succès sur le dépôt Git.")
    except subprocess.CalledProcessError as e:
        log_message(f"Erreur lors de l'opération Git : {e}")

if __name__ == "__main__":
    try:
        with open(LOG_FILENAME, "w", encoding="utf-8") as f:
            f.write(f"--- Début du run : {datetime.now()} ---\n")

        session = create_session()
        flights = fetch_flight_data(session)
        if flights:
            save_to_csv(flights)
            git_commit_and_push()
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Erreur fatale : {e}")
        with open(LOG_FILENAME, "a", encoding="utf-8") as f:
            f.write(f"ERREUR FATALE : {e}\n{error_detail}\n")
        sys.exit(1)