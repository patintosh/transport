from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Fonction cookies ---
def handle_cookies(driver, wait):
    try:
        btn = wait.until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button#onetrust-accept-btn-handler, button.accept-cookies"
            ))
        )
        driver.execute_script("arguments[0].click();", btn)
        print("Cookies acceptés.")
    except Exception:
        print("Pas de cookies à gérer.")

# --- Fonction sélection aéroport ---
def select_airport(wait, selector, airport_code):
    input_elem = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    input_elem.clear()
    input_elem.send_keys(airport_code)

    suggestion = wait.until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            ".autocomplete-list li, .suggestion-item, li[data-code]"
        ))
    )
    suggestion.click()

# --- Fonction principale ---
def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    base_url = "https://book.aircorsica.com/"
    driver.get(base_url)

    wait = WebDriverWait(driver, 25)
    prices = []

    try:
        handle_cookies(driver, wait)
    except Exception:
        pass

    try:
        # 1. Saisie des aéroports
        select_airport(wait, "input[id*='origin'], input[name*='origin'], .origin-input", origen)
        select_airport(wait, "input[id*='destination'], input[name*='destination'], .destination-input", destination)

        # 2. Clic recherche
        bouton_recherche = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                "span.plnext-widget-btn-text, button[type='submit'], .search-btn"))
        )
        driver.execute_script("arguments[0].click();", bouton_recherche)

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
        driver.execute_script("arguments[0].click();", bouton_continuer)

        # 5. Page de vols réelle
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "div.flight-card, div.flight-info, div[id*='flightResults']"))
        )
        print("PAGE DE VOLS CHARGÉE — extraction réelle")

        # 6. Extraction
        lignes_vols = driver.find_elements(By.CSS_SELECTOR,
            "div.flight-card, div.flight-info")

        for ligne in lignes_vols:
            try:
                prix_elem = ligne.find_element(By.CSS_SELECTOR,
                    ".fare-light .fare-price, .fare-cell .fare-price")

                prix_texte = prix_elem.text.replace("€", "").replace(",", ".").strip()
                prix_brut = float(prix_texte)

                if prix_brut > 0:
                    prices.append(prix_brut + 3.0)
            except:
                continue

    except TimeoutException as err:
        print(f"Timeout {origen} -> {destination} le {target_date_str} : {err}")
    except Exception as e:
        print(f"Erreur inattendue {origen} -> {destination} le {target_date_str} : {e}")

    if len(prices) == 0:
        print("⚠️ Extraction vide — aucun vol détecté.")
        return []

    print(f"Extraction réussie : {len(prices)} vols trouvés.")
    return prices
