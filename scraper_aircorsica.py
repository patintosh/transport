from selenium.webdriver.common.by import By
from selenium.webdriver.support import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extraire_prix_light(driver, target_date_str):
    """
    Navigue vers la date cible, valide, puis extrait les prix de la colonne Light
    pour chaque vol disponible.
    """
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Identifier et cliquer sur le bon jour dans le calendrier/sélecteur
        # (Ajuster le sélecteur selon l'élément exact du DOM pour la date J+7)
        xpath_date = f"//td[@data-date='{target_date_str}' or contains(@aria-label, '{target_date_str}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        element_date.click()
        
        # 2. Cliquer sur le bouton Continuer / Valider la date
        bouton_continuer = wait.until(EC.element_to_be_clickable((By.ID, "id_du_bouton_continuer"))) # Remplacer par le bon sélecteur
        bouton_continuer.click()
        
        # 3. Attendre l'affichage des lignes de vols sur la nouvelle page
        wait.until(EC.presence_of_all_elements_located((By.CSSSelector, ".flight-row-selector"))) # Ajuster selon la structure
        
        # 4. Extraire les prix de la colonne Light pour chaque ligne de vol
        prix_light_trouves = []
        lignes_vols = driver.find_elements(By.CSSSelector, ".flight-row-selector")
        
        for ligne in lignes_vols:
            try:
                # Cibler spécifiquement la cellule ou le bouton de la colonne Light
                element_prix = ligne.find_element(By.CSSSelector, ".fare-light .price-amount") # Ajuster le sélecteur
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_light_trouves.append(float(prix_texte))
            except Exception:
                # Ignore si une ligne ne propose pas l'option Light
                continue
                
        return prix_light_trouves

    except Exception as e:
        print(f"Erreur lors de la navigation ou de l'extraction des prix Light : {e}")
        return []
