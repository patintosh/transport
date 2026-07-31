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
    print(f"Erreur critique : Dépendance manquante - {e}")
    sys.exit(1)

CSV_FILENAME = "air_corsica_flights.csv"
LOG_FILENAME = "scraper.log"
USER_DATA_DIR = "./playwright_profile"

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    with open(LOG_FILENAME, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")

def run_scraper():
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    log_message(f"Démarrage du run pour la date cible : {target_date}")
    
    all_flights_data = []
    
    # Définition des deux sens à explorer
    routes_to_check = [
        {"origin": "Ajaccio", "destination": "Paris - Orly", "code": "AJA-ORY"},
        {"origin": "Paris - Orly", "destination": "Ajaccio", "code": "ORY-AJA"}
    ]

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
            viewport={"width": 1920, "height": 1080}
        )
        
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.pages[0] if context.pages else context.new_page()

        try:
            log_message("Navigation vers la page d'accueil d'Air Corsica...")
            page.goto("https://www.aircorsica.com/", wait_until="networkidle", timeout=60000)
            
            # Gestion des cookies
            try:
                cookie_btn = page.locator("button:has-text('Tout accepter'), button:has-text('Accepter')")
                if cookie_btn.count() > 0:
                    cookie_btn.first.click(timeout=3000)
                    log_message("Bandeau de cookies accepté.")
            except Exception:
                pass

            for route in routes_to_check:
                route_code = route["code"]
                log_message(f"Traitement de la liaison : {route_code}")

                # Simulation de la recherche pour chaque sens
                try:
                    page.click("text=Aller simple", timeout=5000)
                    
                    # Saisie départ / arrivée
                    page.fill("input[name*='departure'], input[placeholder*='Départ']", route["origin"])
                    page.click(f"text={route['origin']}")
                    
                    page.fill("input[name*='arrival'], input[placeholder*='Arrivée']", route["destination"])
                    page.click(f"text={route['destination']}")

                    # Sélection de la date J+7
                    page.click("input[name*='date'], .calendar-input")
                    date_selector = f"[data-date='{target_date}'], td[title*='{target_date}']"
                    page.click(date_selector, timeout=5000)

                    # Lancement de la recherche
                    page.click("button:has-text('Rechercher'), input[value*='Rechercher']")
                    page.wait_for_load_state("networkidle", timeout=30000)

                    # Sélection du jour dans la grille tarifaire
                    page.click(f"[data-date='{target_date}'] .cell-price, .day-cell:has-text('{target_date.split('-')[-1]}')", timeout=5000)
                    page.click("button:has-text('Continuer'), .btn-continue", timeout=5000)
                    page.wait_for_load_state("networkidle", timeout=30000)

                    content = page.content()
                    if "Pardon Our Interruption" in content or "Access Denied" in content:
                        log_message("ALERTE : Blocage de sécurité détecté.")
                        break

                    soup = BeautifulSoup(content, "html.parser")
                    flight_rows = soup.find_all("div", class_=re.compile("flight-row|row-flight|row-reco", re.I))
                    
                    # SÉCURITÉ : Si N = 0, aucun vol proposé par le transporteur à cette date
                    if not flight_rows or len(flight_rows) == 0:
                        log_message(f"Aucun vol disponible détecté pour {route_code} à la date {target_date}. Aucun prix enregistré pour cette liaison.")
                        # Retour en arrière ou rechargement propre pour la liaison suivante si nécessaire
                        page.goto("https://www.aircorsica.com/", wait_until="networkidle", timeout=30000)
                        continue

                    log_message(f"Nombre de vols (N) détectés pour {route_code} : {len(flight_rows)}")
                    route_flights_extracted = 0

                    for row in flight_rows:
                        time_elem = row.find(class_=re.compile("time|departure-time", re.I))
                        flight_time = time_elem.get_text(strip=True) if time_elem else "Inconnu"

                        light_cell = row.find("div", class_=re.compile("cell-reco|fare-light", re.I))
                        if light_cell:
                            price_elem = light_cell.find(class_=re.compile("price|integer|amount", re.I))
                            if price_elem:
                                price_val = price_elem.get_text(strip=True)
                                clean_price = re.sub(r'[^\d.,]', '', price_val.replace(',', '.'))
                                try:
                                    if float(clean_price) > 0.0:
                                        formatted_price = f"{price_val} EUR" if "EUR" not in price_val and "€" not in price_val else price_val
                                        all_flights_data.append({
                                            "Date_Recherche": datetime.now().strftime("%Y-%m-%d"),
                                            "Date_Vol": target_date,
                                            "Route": route_code,
                                            "Horaire": flight_time,
                                            "Tarif": formatted_price
                                        })
                                        route_flights_extracted += 1
                                except ValueError:
                                    pass

                    log_message(f"Succès pour {route_code} : {route_flights_extracted} tarifs Light récupérés.")
                    
                    # Retour à l'accueil pour la liaison suivante
                    page.goto("https://www.aircorsica.com/", wait_until="networkidle", timeout=30000)

                except Exception as e:
                    log_message(f"Erreur lors du traitement de la liaison {route_code} : {e}")
                    try:
                        page.goto("https://www.aircorsica.com/", wait_until="networkidle", timeout=30000)
                    except Exception:
                        break

        except Exception as e:
            log_message(f"Erreur critique Playwright : {e}")
        finally:
            context.close()

    return all_flights_data

def save_to_csv_top(data):
    if not data:
        return
        
    existing_rows = []
    fieldnames = ["Date_Recherche", "Date_Vol", "Route", "Horaire", "Tarif"]
    
    if os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
    
    all_rows = data + existing_rows
    
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
            
    log_message("Données insérées en haut du fichier CSV.")

def git_push():
    try:
        subprocess.run(["git", "add", CSV_FILENAME], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update flights {datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        log_message("Mise à jour poussée sur Git avec succès.")
    except subprocess.CalledProcessError as e:
        log_message(f"Erreur Git : {e}")

if __name__ == "__main__":
    with open(LOG_FILENAME, "w", encoding="utf-8") as f:
        f.write(f"--- Début du run : {datetime.now()} ---\n")
        
    records = run_scraper()
    if records:
        save_to_csv_top(records)
        git_push()
    else:
        log_message("Aucun vol trouvé ou échec général sur l'ensemble des liaisons ce jour.")