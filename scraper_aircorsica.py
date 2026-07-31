import os
import sys
import csv
import re
import subprocess
from datetime import datetime, timedelta

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
USER_DATA_DIR = "./playwright_profile"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    with open(LOG_FILENAME, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")

def fetch_flight_data_with_playwright():
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    log_message(f"Recherche des vols pour la date : {target_date} avec les paramètres Amadeus officiels")
    
    flights = []
    
    # URL construite exactement selon la structure des vrais prix Amadeus fournie
    search_url = (
        f"{BASE}/FlexPricerAvailabilityDispatcherPui.action"
        f"?BOOKING_FLOW=REVENUE"
        f"&COUNTRY_SITE=FR"
        f"&LANGUAGE=FR"
        f"&OFFICE_ID=AJAXK08AB"
        f"&PAGE_ID=FPOW"
        f"&SITE=BDEQBNEW"
        f"&TRIP_FLOW=YES"
        f"&DATE={target_date}"
    )

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="fr-FR",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            extra_http_headers={
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"'
            }
        )
        
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.pages[0] if context.pages else context.new_page()

        try:
            log_message("Navigation directe vers la grille tarifaire Amadeus...")
            page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            # Surveillance active du challenge Imperva
            for attempt in range(5):
                content = page.content()
                if "Pardon Our Interruption" not in content and "Access Denied" not in content and "_Incapsula_Resource" not in content:
                    break
                log_message(f"Challenge Imperva détecté (tentative {attempt + 1}/5), attente de résolution...")
                page.wait_for_timeout(4000)

            content = page.content()
            
            if "Pardon Our Interruption" in content or "Access Denied" in content or "_Incapsula_Resource" in content:
                log_message("ALERTE : Blocage persistant d'Imperva.")
                with open("imperva_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                context.close()
                return flights

            soup = BeautifulSoup(content, "html.parser")
            extracted_prices = []
            
            # Extraction affinée sur la famille de prix "Light" et filtrage des valeurs réalistes (> 50 EUR)
            for cell in soup.find_all("div", class_="cell-reco"):
                name_elem = cell.find("span", class_="cell-reco-fareFamilyName")
                if name_elem and "light" in name_elem.get_text(strip=True).lower():
                    price_elem = cell.find("span", class_="cell-reco-bestprice-integer")
                    if price_elem:
                        val = price_elem.get_text(strip=True)
                        extracted_prices.append(val)

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
                            # Nettoyage et vérification pour ignorer les bannières publicitaires (< 50€)
                            clean_val = re.sub(r'[^\d.,]', '', val.replace(',', '.'))
                            if clean_val:
                                try:
                                    if float(clean_val) > 50.0:
                                        extracted_prices.append(val)
                                        break
                                except ValueError:
                                    pass
                        parent = parent.parent

            unique_prices = list(dict.fromkeys(extracted_prices))

            if unique_prices:
                formatted_price = f"{unique_prices[0]} EUR" if "EUR" not in unique_prices[0] and "€" not in unique_prices[0] else unique_prices[0]
                log_message(f"Tarif Light valide extrait : {formatted_price}")
                flights.append({"Date": target_date, "Route": "AJA-ORY", "Price": formatted_price})
            else:
                log_message("Aucun prix valide supérieur à 50€ trouvé sur la page.")
                with open("no_prices_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            log_message(f"Erreur durant l'exécution Playwright : {e}")
        finally:
            context.close()

    return flights

def save_to_csv(data):
    if not data:
        return
        
    existing_rows = []
    if os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
    
    all_rows = data + existing_rows
    
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Route", "Price"])
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
            
    log_message("Données enregistrées en haut du fichier CSV.")

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
            log_message("Aucune donnée valide à enregistrer. Commit Git ignoré.")
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Erreur fatale : {e}")
        with open(LOG_FILENAME, "a", encoding="utf-8") as f:
            f.write(f"ERREUR FATALE : {e}\n{error_detail}\n")
        sys.exit(1)