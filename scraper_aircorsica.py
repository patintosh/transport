import csv
from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration des routes et paramètres
ROUTES = [
    ("ORY", "AJA"),
    ("ORY", "BIA"),
    ("ORY", "CLY"),
    ("ORY", "FSC")
]

CSV_FILE = "aircorsica_prices.csv"

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # User-agent pour éviter d'être bloqué
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_route(driver, origen, destination, target_date_str):
    """
    Exécute la recherche, navigue vers la date J+7 et extrait les prix réels de la colonne Light.
    """
    # URL de base de recherche (ajustable selon votre point d'entrée initial)
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)
    
    wait = WebDriverWait(driver, 20)
    prices = []
    
    try:
        # NOTE : Insérez ici vos étapes initiales de sélection de l'itinéraire (Origine/Destination) 
        # si vous partez de la page d'accueil globale, ou utilisez directement l'URL avec paramètres si fixe.
        
        # 1. Attente et sélection de la date J+7 dans le calendrier dynamique
        # (Ajustez le xpath selon l'attribut exact du calendrier, ex: data-date ou aria-label)
        xpath_date = f"//td[@data-date='{target_date_str}' or contains(@aria-label, '{target_date_str}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        element_date.click()
        
        # 2. Validation / Clic sur Continuer pour charger la page des disponibilités par vol
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSSSelector, "#id_du_bouton_continuer, button.submit-dates, .dialog-button"))
        )
        bouton_continuer.click()
        
        # 3. Attente active du chargement complet des lignes de vols de la SPA Amadeus
        # On cible les conteneurs de lignes de vols injectés par le moteur
        lignes_vols = wait.until(
            EC.presence_of_all_elements_located((By.CSSSelector, ".flight-row, .flight-item, [data-component*='Flight']"))
        )
        
        # 4. Extraction ciblée des prix de la colonne "Light" (première formule tarifaire)
        for ligne in lignes_vols:
            try:
                # Ciblage spécifique du montant dans la première colonne tarifaire (Light)
                element_prix = ligne.find_element(By.CSSSelector, ".fare-light .price-amount, .brand-column-0 .price, .fare-light-value")
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_float = float(prix_texte)
                if prix_float > 0:
                    prices.append(prix_float)
            except Exception:
                # Ignore si une ligne spécifique ne permet pas l'extraction directe
                continue
                
    except Exception as e:
        print(f"Erreur lors du scraping de {origen} vers {destination} pour le {target_date_str} : {e}")
        
    return prices

def main():
    driver = init_driver()
    
    # Calcul de la date J+7
    date_capture = datetime.now().strftime("%Y-%m-%d")
    target_date = datetime.now() + timedelta(days=7)
    target_date_str = target_date.strftime("%Y-%m-%d") # Format yyyy-mm-dd
    target_date_display = target_date.strftime("%d/%0m/%Y") # Format affiché dd/mm/yyyy
    
    rows_to_save = []
    
    try:
        for origen, destination in ROUTES:
            print(f"Traitement : {origen} -> {destination} pour le {target_date_str}")
            
            prices = scrape_route(driver, origen, destination, target_date_str)
            
            if prices:
                prix_min = min(prices)
                prix_max = max(prices)
                prix_moyen = round(sum(prices) / len(prices), 2)
                nombre_vols = len(prices)
            else:
                # Valeurs par défaut si aucun prix n'a pu être extrait proprement
                prix_min = 0.0
                prix_max = 0.0
                prix_moyen = 0.0
                nombre_vols = 0
                
            rows_to_save.append([
                date_capture,
                origen,
                destination,
                target_date_display,
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
