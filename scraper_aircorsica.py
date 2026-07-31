from datetime import datetime, timedelta
import os
import csv
from playwright.sync_api import sync_playwright

def run_scraper():
    routes = [
        {"code": "AJA-ORY", "origin": "AJA", "destination": "ORY"},
        {"code": "ORY-AJA", "origin": "ORY", "destination": "AJA"}
    ]
    
    target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
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
                    
                    # Fermeture/Acceptation de la bannière de cookies si elle apparaît
                    try:
                        cookie_selectors = [
                            "button:has-text('Tout accepter')",
                            "button:has-text('Accepter')",
                            "#tarteaucitronAllAllowed",
                            ".cookie-accept",
                            "button[id*='cookie']"
                        ]
                        for selector in cookie_selectors:
                            btn = page.locator(selector).first
                            if btn.is_visible(timeout=2000):
                                btn.click()
                                print("Bannière de cookies fermée.")
                                break
                    except Exception:
                        pass # Pas de cookies ou déjà acceptés
                    
                    # Clic sur le label visible associé au bouton radio aller simple
                    travel_type_label = page.locator("label[for='edit-booking-flight-v2-travel-type-o']")
                    travel_type_label.scroll_into_view_if_needed()
                    travel_type_label.click(timeout=5000)
                    
                    # Sélection des aéroports via les balises <select> natives
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