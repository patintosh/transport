import os
import sqlite3
import csv
import subprocess
from datetime import datetime, timedelta
from curl_cffi import requests

BASE = "https://book.aircorsica.com/plnext/AirCorsicaDX"
CSV_FILENAME = "air_corsica_flights.csv"

def load_chrome_cookies(profile_path):
    """Extrait les cookies du profil Chrome local (SQLite)"""
    cookies_file = os.path.join(profile_path, "Default", "Network", "Cookies")
    if not os.path.exists(cookies_file):
        cookies_file = os.path.join(profile_path, "Default", "Cookies")
    
    cookies = {}
    if not os.path.exists(cookies_file):
        print(f"Fichier de cookies introuvable à : {cookies_file}")
        return cookies

    try:
        # Copie temporaire pour éviter les conflits de verrouillage si Chrome est ouvert
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
    # Chemin par défaut du profil Chrome sur macOS
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

    # Initialisation indispensable via Preload.action
    init_url = f"{BASE}/Preload.action?LANGUAGE=FR&SITE=BDEQBNEW"
    r = s.get(init_url, headers=headers)
    print(f"Statut d'initialisation (Preload) : {r.status_code}")

    return s

def fetch_flight_data(session):
    """Récupère les données de vol (J+7)"""
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"Recherche des vols pour la date : {target_date}")

    # Exemple de requête vers le moteur de disponibilité
    # (Adaptez les paramètres selon les charges utiles nécessaires de votre flux)
    search_url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action"
    
    # Payload ou paramètres de recherche (exemple type)
    params = {
        "DATE": target_date,
        "LANGUAGE": "FR",
        "SITE": "BDEQBNEW"
    }

    r = session.get(search_url, params=params)
    print(f"Statut de la requête de vol : {r.status_code}")
    
    # Simulation d'extraction de données (à adapter selon le parsing HTML/JSON souhaité)
    flights = [
        {"Date": target_date, "Route": "AJA-ORY", "Price": "120.00 EUR"},
        {"Date": target_date, "Route": "BIA-MRS", "Price": "85.00 EUR"}
    ]
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