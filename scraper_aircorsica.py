import csv
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    """
    Exécute la recherche, sélectionne la date J+7 et extrait les prix réels de la SPA Amadeus.
    """
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)
    
    wait = WebDriverWait(driver, 20)
    prices = []
    
    try:
        # 1. Sélection de la date J+7 via l'aria-label dynamique de l'input caché
        xpath_date = f"//input[contains(@aria-label, '{target_date_display}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        driver.execute_script("arguments[0].click();", element_date)
        
        # 2. Validation / Clic sur le bouton Continuer
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSSSelector, "span.plnext-widget-btn-text"))
        )
        bouton_continuer.click()
        
        # 3. Attente active du chargement complet des lignes de vols de la SPA Amadeus
        lignes_vols = wait.until(
            EC.presence_of_all_elements_located((By.CSSSelector, ".flight-row, .flight-item, [data-component*='Flight']"))
        )
        
        # 4. Extraction ciblée des prix de la colonne "Light"
        for ligne in lignes_vols:
            try:
                element_prix = ligne.find_element(By.CSSSelector, ".fare-light .price-amount, .brand-column-0 .price, .fare-light-value, .price-amount")
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_float = float(prix_texte)
                if prix_float > 0:
                    prices.append(prix_float)
            except Exception:
                continue
                
    except Exception as e:
        print(f"Erreur lors du scraping de {origen} vers {destination} pour le {target_date_str} : {e}")
        
    return prices

def main():
    driver = init_driver()
    
    date_capture = datetime.now().strftime("%Y-%m-%d")
    target_date = datetime.now() + timedelta(days=7)
    target_date_str = target_date.strftime("%Y-%m-%d")
    
    # Formatage de la date en français pour correspondre à l'aria-label (ex: "06 Août 2026")
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
        
    # Écriture dans le fichier CSV (sans la colonne TIME)
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date_Capture_Seule", "Départ", "Arrivée", "Date vol", "Prix_Min", "Prix_Moyen", "Prix_Max", "Nombre_Vols"])
        writer.writerows(rows_to_save)
        
    print("Mise à jour du CSV terminée avec succès.")

if __name__ == "__main__":
    main()
