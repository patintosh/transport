import csv
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

ROUTES = [
    ("ORY", "AJA"),
    ("ORY", "BIA"),
    ("ORY", "CLY"),
    ("ORY", "FSC")
]

CSV_FILE = "aircorsica_prices.csv"

MONTHS_FR = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    return driver

def handle_cookies(driver, wait):
    try:
        cookie_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#didomi-notice-agree-button, button[id*='accept'], .cookie-accept-btn"))
        )
        cookie_button.click()
    except TimeoutException:
        pass

def select_airport(wait, input_selector, airport_code):
    input_elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector)))
    input_elem.click()
    input_elem.clear()
    input_elem.send_keys(airport_code)
    
    suggestion = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//li[contains(., '{airport_code}')] | //div[contains(@class, 'suggestion') and contains(., '{airport_code}')]"))
    )
    suggestion.click()

def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)
    
    wait = WebDriverWait(driver, 25)
    prices = []
    
    handle_cookies(driver, wait)
    
    try:
        # 1. Saisie des aéroports sur la page d'accueil
        select_airport(wait, "input[id*='origin'], input[name*='origin'], .origin-input", origen)
        select_airport(wait, "input[id*='destination'], input[name*='destination'], .destination-input", destination)

        # 2. Clic pour aller sur le tableau des dates
        bouton_recherche = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.plnext-widget-btn-text, button[type='submit'], .search-btn"))
        )
        bouton_recherche.click()
        
        # 3. Sélection de la date J+7 dans le tableau
        xpath_date = f"//input[contains(@aria-label, '{target_date_display}')] | //div[contains(@aria-label, '{target_date_display}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        driver.execute_script("arguments[0].click();", element_date)
        
        # 4. Clic sur Continuer pour accéder à la liste des vols
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.continue-btn, span.plnext-widget-btn-text, .btn-continue"))
        )
        bouton_continuer.click()
        
        # 5. VERROU STRICT : Attente exclusive du conteneur de résultats de vols Amadeus
        # Empêche catégoriquement toute lecture tant que la page de vol n'est pas chargée
        lignes_vols = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class*='flight-line'], tr[class*='flight'], div[class*='fare-family-item'], .travel-option-row"))
        )
        
        # 6. Extraction exclusive de la colonne Light sur la page finale
        for ligne in lignes_vols:
            try:
                element_prix = ligne.find_element(By.CSS_SELECTOR, ".brand-column-0 .price-amount, td.fare-light .price, .fare-light-value, [class*='fare-light'] span[class*='price']")
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_float = float(prix_texte)
                if prix_float > 0:
                    prices.append(prix_float)
            except Exception:
                continue
                
    except TimeoutException as err:
        print(f"Erreur Timeout pour {origen} -> {destination} le {target_date_str} : {err}")
    except Exception as e:
        print(f"Erreur inattendue pour {origen} -> {destination} le {target_date_str} : {e}")
        
    return prices

def main():
    driver = init_driver()
    
    date_capture = datetime.now().strftime("%Y-%m-%d")
    target_date = datetime.now() + timedelta(days=7)
    target_date_str = target_date.strftime("%Y-%m-%d")
    target_date_display = f"{target_date.day:02d} {MONTHS_FR[target_date.month]} {target_date.year}"
    
    rows_to_save = []
    
    try:
        for origen, destination in ROUTES:
            print(f"Traitement : {origen} -> {destination} pour le {target_date_str} (J+7)")
            
            prices = scrape_route(driver, origen, destination, target_date_str, target_date_display)
            
            if prices:
                prix_min = min(prices)
                prix_max = max(prices)
                prix_moyen = round(sum(prices) / len(prices), 2)
                nombre_vols = len(prices)
            else:
                prix_min = 0.0
                prix_max = 0.0
                prix_moyen = 0.0
                nombre_vols = 0
                
            rows_to_save.append([
                date_capture,
                origen,
                destination,
                target_date_str,
                prix_min,
                prix_moyen,
                prix_max,
                nombre_vols
            ])
            
    finally:
        driver.quit()
        
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date_Capture_Seule", "Départ", "Arrivée", "Date vol", "Prix_Min", "Prix_Moyen", "Prix_Max", "Nombre_Vols"])
        writer.writerows(rows_to_save)
        
    print("Mise à jour du CSV terminée avec succès.")

if __name__ == "__main__":
    main()
