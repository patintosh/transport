def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)

    wait = WebDriverWait(driver, 25)
    prices = []

    handle_cookies(driver, wait)

    try:
        # 1. Saisie des aéroports
        select_airport(wait, "input[id*='origin'], input[name*='origin'], .origin-input", origen)
        select_airport(wait, "input[id*='destination'], input[name*='destination'], .destination-input", destination)

        # 2. Clic recherche
        bouton_recherche = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "span.plnext-widget-btn-text, button[type='submit'], .search-btn"))
        )
        bouton_recherche.click()

        # 3. Sélection de la date
        xpath_date = (
            f"//input[contains(@aria-label, '{target_date_display}')] | "
            f"//div[contains(@aria-label, '{target_date_display}')] | "
            f"//td[contains(@aria-label, '{target_date_display}')]"
        )
        element_date = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_date)))
        driver.execute_script("arguments[0].click();", element_date)

        # 4. Bouton continuer
        bouton_continuer = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "button.continue-btn, span.plnext-widget-btn-text, .btn-continue"))
        )
        bouton_continuer.click()

        # 5. VERROU STRICT : attendre un élément qui n'existe QUE sur la vraie page de vols
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "div.flight-card, div.flight-info, div[id*='flightResults']"))
        )

        # 6. Extraction des vrais vols (jamais les pubs)
        lignes_vols = driver.find_elements(By.CSS_SELECTOR,
            "div.flight-card, div.flight-info")

        for ligne in lignes_vols:
            try:
                # Colonne Light uniquement
                prix_elem = ligne.find_element(By.CSS_SELECTOR,
                    ".fare-cell .fare-price, .fare-light .fare-price")

                prix_texte = prix_elem.text.replace("€", "").replace(",", ".").strip()
                prix_brut = float(prix_texte)

                if prix_brut > 0:
                    prices.append(prix_brut + 3.0)  # frais obligatoires
            except:
                continue

    except TimeoutException as err:
        print(f"Timeout {origen} -> {destination} le {target_date_str} : {err}")
    except Exception as e:
        print(f"Erreur inattendue {origen} -> {destination} le {target_date_str} : {e}")

    return prices
