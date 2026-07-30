import csv
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, AttributeError

ROUTES = [
    ("ORY", "AJA"),
    ("ORY", "BIA"),
    ("ORY", "CLY"),
    ("ORY", "FSC")
]

CSV_FILE = "aircorsica_prices.csv"

# Dictionnaire pour s'affranchir de la locale système dans GitHub Actions pour les aria-label
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
    """Gère le bandeau de consentement aux cookies pour éviter les interceptions de clics."""
    try:
        cookie_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#didomi-notice-agree-button, button[id*='accept'], .cookie-accept-btn"))
        )
        cookie_button.click()
    except TimeoutException:
        pass  # Aucun bandeau détecté ou déjà accepté

def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    """
    Exécute la recherche, gère les cookies, renseigne les aéroports, 
    sélectionne la date J+7 et extrait les prix réels de la SPA Amadeus.
    """
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)
    
    wait = WebDriverWait(driver, 20)
    prices = []
    
    # 1. Traitement des cookies en amont
    handle_cookies(driver, wait)
    
    try:
        # 2. Saisie des aéroports de départ et d'arrivée
        try:
            input_origin = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id*='origin'], input[name*='origin'], .origin-input")))
            input_origin.clear()
            input_origin.send_keys(origen)
            
            input_dest = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id*='destination'], input[name*='destination'], .destination-input")))
            input_dest.clear()
            input_dest.send_keys(destination)
        except Exception as e:
            print(f"Note sur la saisie des aéroports ({origen} -> {destination}) : {e}")

        # 3. Sélection de la date J+7 via l'aria-label dynamique
        xpath_date = f"//input[contains(@aria-label, '{target_date_display}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        driver.execute_script("arguments[0].click();", element_date)
        
        # 4. Validation / Clic sur le bouton Continuer (Utilisation de By.CSS_SELECTOR corrigé)
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.plnext-widget-btn-text"))
        )
        bouton_continuer.click()
        
        # 5. Attente active du chargement complet des lignes de vols
        lignes_vols = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".flight-row, .flight-item, [data-component*='Flight']"))
        )
        
        # 6. Extraction ciblée des prix de la colonne "Light"
        for ligne in lignes_vols:
            try:
                element_prix = ligne.find_element(By.CSS_SELECTOR, ".fare-light .price-amount, .brand-column-0 .price, .fare-light-value, .price-amount")
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_float = float(prix_texte)
                if prix_float > 0:
                    prices.append(prix_float)
            except Exception:
                continue
                
    except (TimeoutException, AttributeError) as err:
        print(f"Erreur ciblée (Timeout ou Attribut) pour {origen} -> {destination} le {target_date_str} : {err}")
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
            print(f"Traitement : {origen} -> {destination} pour le {target_date_str}")
            
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
