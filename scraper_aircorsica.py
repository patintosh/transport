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

        # 2. Premier clic : Validation de la recherche pour afficher le calendrier des dates
        bouton_recherche = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.plnext-widget-btn-text, button[type='submit'], .search-btn"))
        )
        bouton_recherche.click()
        
        # 3. Sélection de la date J+7 dans le tableau des dates
        xpath_date = f"//input[contains(@aria-label, '{target_date_display}')] | //div[contains(@aria-label, '{target_date_display}')] | //td[contains(@aria-label, '{target_date_display}')]"
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        driver.execute_script("arguments[0].click();", element_date)
        
        # 4. Deuxième clic : Bouton Continuer pour quitter le calendrier et charger les vols
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.continue-btn, span.plnext-widget-btn-text, .btn-continue"))
        )
        bouton_continuer.click()
        
        # 5. VERROU STRICT DE NAVIGATION : On s'assure d'être sur la page de résultats (par ex. présence d'un conteneur de vol spécifique)
        # On attend un élément qui n'existe PAS sur la page d'accueil
        lignes_vols = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.flight-list-item, tr.flight-row, .travel-option-container"))
        )
        
        # 6. Extraction exclusive de la colonne Light sur la vraie page de vols + Ajout des 3€ de frais
        for ligne in lignes_vols:
            try:
                element_prix = ligne.find_element(By.CSS_SELECTOR, ".brand-column-0 .price-amount, td.fare-light .price, .fare-light-value")
                prix_texte = element_prix.text.replace("€", "").replace(",", ".").strip()
                prix_brut = float(prix_texte)
                if prix_brut > 0:
                    prix_final = prix_brut + 3.0  # Ajout obligatoire des frais d'émission
                    prices.append(prix_final)
            except Exception:
                continue
                
    except TimeoutException as err:
        print(f"Erreur Timeout pour {origen} -> {destination} le {target_date_str} : {err}")
    except Exception as e:
        print(f"Erreur inattendue pour {origen} -> {destination} le {target_date_str} : {e}")
        
    return prices
