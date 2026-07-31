import os
import sys
import csv
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
    """Utilise Playwright pour contourner Imperva et extraire précisément le tarif Light"""
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
            page.wait_for_timeout(4000)

            log_message("Navigation vers la page de résultats de vol...")
            page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            try:
                # Augmentation du délai d'attente à 30 secondes pour laisser le temps au rendu Amadeus
                page.wait_for_selector(".cell-reco", timeout=30000)
                page.wait_for_timeout(3000)
            except Exception:
                log_message("Délai d'attente dépassé pour les blocs tarifaires, analyse du contenu actuel.")

            content = page.content()
            
            if "Pardon Our Interruption" in content or "Access Denied" in content or "captcha" in content.lower():
                log_message("ALERTE : Blocage persistant détecté dans la page finale.")
                with open("imperva_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                return flights

            # Sauvegarde du HTML pour diagnostic
            with open("availability_debug.html", "w", encoding="utf-8") as f:
                f.write(content)

            soup = BeautifulSoup(content, "html.parser")
            
            extracted_prices = []
            
            # Ciblage chirurgical des blocs de prix Amadeus par famille de tarif ("Light")
            for cell in soup.find_all("div", class_="cell-reco"):
                name_elem = cell.find("span", class_="cell-reco-fareFamilyName")
                if name_elem and name_elem.get_text(strip=True).lower() == "light":
                    price_elem = cell.find("span", class_="cell-reco-bestprice-integer")
                    if price_elem:
                        price = f"{price_elem.get_text(strip=True)} €"
                        extracted_prices.append(price)

            if extracted_prices:
                log_message(f"Tarif(s) Light extrait(s) avec succès : {extracted_prices}")
                for price in extracted_prices:
                    flights.append({"Date": target_date, "Route": "AJA-ORY", "Price": price})
            else:
                log_message("Tarif Light non trouvé via les sélecteurs stricts, utilisation du statut de disponibilité.")
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