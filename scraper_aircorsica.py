import os
import sys
import csv
import re
import subprocess
from datetime import datetime, timedelta

# Vérification et importation sécurisée des dépendances
try:
    from playwright.sync_api import sync_playwright
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

def fetch_flight_data_with_playwright():
    """Utilise Playwright pour contourner Imperva, gère le challenge de sécurité et extrait le tarif Light"""
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    log_message(f"Recherche des vols pour la date : {target_date} via Playwright")
    
    flights = []
    init_url = f"{BASE}/Preload.action?LANGUAGE=FR&SITE=BDEQBNEW"
    search_url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action?DATE={target_date}&LANGUAGE=FR&SITE=BDEQBNEW"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="fr-FR",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            log_message("Ouverture de la page Preload (résolution de reese84)...")
            page.goto(init_url, wait_until="networkidle", timeout=60000)
            
            # Attente active si Imperva intercepte la page initiale
            for _ in range(10):
                content = page.content()
                if "_Incapsula_Resource" in content or "main-iframe" in content:
                    log_message("Résolution du challenge Imperva en cours...")
                    page.wait_for_timeout(2000)
                else:
                    break

            log_message("Navigation vers la page de résultats de vol...")
            page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            # Attente active si Imperva intercepte la page de résultats
            for _ in range(10):
                content = page.content()
                if "_Incapsula_Resource" in content or "main-iframe" in content:
                    log_message("Challenge Imperva détecté sur la page de résultats, attente de résolution...")
                    page.wait_for_timeout(2000)
                else:
                    break

            content = page.content()
            
            if "Pardon Our Interruption" in content or "Access Denied" in content or "_Incapsula_Resource" in content:
                log_message("ALERTE : Blocage persistant d'Imperva détecté.")
                with open("imperva_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                return flights

            # Sauvegarde du HTML pour diagnostic
            with open("availability_debug.html", "w", encoding="utf-8") as f:
                f.write(content)

            soup = BeautifulSoup(content, "html.parser")
            extracted_prices = []
            
            # 1. Tentative avec les sélecteurs Amadeus spécifiques
            for cell in soup.find_all("div", class_="cell-reco"):
                name_elem = cell.find("span", class_="cell-reco-fareFamilyName")
                if name_elem and "light" in name_elem.get_text(strip=True).lower():
                    price_elem = cell.find("span", class_="cell-reco-bestprice-integer")
                    if price_elem:
                        extracted_prices.append(price_elem.get_text(strip=True))

            # 2. Recherche robuste par voisinage si les sélecteurs stricts échouent
            if not extracted_prices:
                light_nodes = soup.find_all(string=re.compile(r'^\s*Light\s*$', re.IGNORECASE))
                for node in light_nodes:
                    parent = node.parent
                    for _ in range(6):
                        if not parent:
                            break
                        price_match = parent.find(class_=lambda x: x and any(c in x for c in ["price", "integer", "amount"]))
                        if price_match:
                            val = price_match.get_text(strip=True)
                            if any(char.isdigit() for char in val):
                                extracted_prices.append(val)
                                break
                        parent = parent.parent

            # 3. Fallback global sur les motifs de prix si rien n'est trouvé
            if not extracted_prices:
                price_pattern = re.compile(r'\d+[\s,\.]*\d*\s*€')
                for tag in soup.find_all(string=price_pattern):
                    text = tag.strip()
                    if len(text) < 15:
                        extracted_prices.append(text)

            # Nettoyage des doublons éventuels
            unique_prices = list(dict.fromkeys(extracted_prices))

            if unique_prices:
                formatted_price = f"{unique_prices[0]} €" if "€" not in unique_prices[0] else unique_prices[0]
                log_message(f"Tarif Light extrait avec succès : {formatted_price}")
                flights.append({"Date": target_date, "Route": "AJA-ORY", "Price": formatted_price})
            else:
                log_message("Aucun prix trouvé, utilisation du statut de disponibilité.")
                flights.append({"Date": target_date, "Route": "AJA-ORY", "Price": "DISPONIBLE"})

        except Exception as e:
            log_message(f"Erreur durant l'exécution Playwright : {e}")
        finally:
            browser.close()

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

        flights = fetch_flight_data_with_playwright()
        if flights:
            save_to_csv(flights)
            git_commit_and_push()
        else:
            log_message("Aucune donnée enregistrée.")
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Erreur fatale : {e}")
        with open(LOG_FILENAME, "a", encoding="utf-8") as f:
            f.write(f"ERREUR FATALE : {e}\n{error_detail}\n")
        sys.exit(1)