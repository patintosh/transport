from datetime import datetime, timedelta
import os
import csv
from playwright.sync_api import sync_playwright

def run_scraper():
    # Définition des liaisons avec les codes IATA
    routes = [
        {"code": "AJA-ORY", "origin": "AJA", "destination": "ORY"},
        {"code": "ORY-AJA", "origin": "ORY", "destination": "AJA"}
    ]
    
    # Calcul de la date J+7
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Répertoire du profil persistant pour assurer la stabilité et éviter les blocages anti-bot
    user_data_dir = os.path.expanduser("~/.aircorsica_browser_profile")
    
    csv_filename = "air_corsica_prices.csv"
    file_exists = os.path.isfile(csv_filename)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=["--headless=new", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        
        with open(csv_filename, mode="a", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            if not file_exists:
                writer.writerow(["Date", "Route", "Price"])
            
            for route in routes:
                try:
                    print(f"Traitement de la route {route['code']} pour le {target_date}...")
                    page.goto("https://www.aircorsica.com/", wait_until="networkidle", timeout=60000)
                    
                    # Sélection du type de parcours "Aller simple"
                    page.click("#edit-booking-flight-v2-travel-type-o", timeout=5000)
                    
                    # Sélection directe des aéroports via les balises <select> natives cachées par Select2
                    page.select_option("#edit-booking-flight-v2-from", route["origin"])
                    page.select_option("#edit-booking-flight-v2-to", route["destination"])
                    
                    # Saisie de la date de départ
                    page.fill("#edit-booking-flight-v2-departure-date", target_date)
                    
                    # Déclenchement de la recherche
                    page.keyboard.press("Enter")
                    page.wait_for_load_state("networkidle", timeout=30000)
                    
                    # Extraction du tarif
                    price = "N/A"
                    try:
                        price_element = page.locator(".price, .flight-price, [class*='price']").first
                        if price_element.is_visible(timeout=10000):
                            price = price_element.inner_text().strip()
                    except Exception:
                        pass
                    
                    writer.writerow([target_date, route["code"], price])
                    print(f"Succès : {route['code']} -> Prix : {price}")
                    
                except Exception as e:
                    print(f"Erreur lors du traitement de la route {route['code']} : {e}")
                    writer.writerow([target_date, route["code"], "ERROR"])
                    
        context.close()

if __name__ == "__main__":
    run_scraper()