from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Cookies ---
def handle_cookies(driver, wait):
    try:
        btn = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        driver.execute_script("arguments[0].click();", btn)
        print("Cookies acceptés.")
    except:
        print("Pas de cookies à gérer.")

# --- Sélection aéroport ---
def select_airport(wait, field_id, list_selector, airport_code):
    field = wait.until(EC.element_to_be_clickable((By.ID, field_id)))
    field.clear()
    field.send_keys(airport_code)

    suggestion = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, list_selector))
    )
    suggestion.click()

# --- Scraper principal ---
def scrape_route(driver, origen, destination, target_date_str, target_date_display):
    driver.get("https://book.aircorsica.com/")
    wait = WebDriverWait(driver, 30)
    prices = []

    try:
        handle_cookies(driver, wait)

        # 1. Origine
        select_airport(
            wait,
            "origin-input",
            "ul#origin-list li",
            origen
        )

        # 2. Destination
        select_airport(
            wait,
            "destination-input",
            "ul#destination-list li",
            destination
        )

        # 3. Recherche
        search_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "search-button"))
        )
        driver.execute_script("arguments[0].click();", search_btn)

        # 4. Date
        date_cell = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"td[data-date='{target_date_str}']"))
        )
        driver.execute_script("arguments[0].click();", date_cell)

        # 5. Continuer
        continue_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "continue-button"))
        )
        driver.execute_script("arguments[0].click();", continue_btn)

        # 6. Page de vols
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.flight-card"))
        )
        print("PAGE DE VOLS CHARGÉE — extraction réelle")

        # 7. Extraction
        cards = driver.find_elements(By.CSS_SELECTOR, "div.flight-card")

        for card in cards:
            try:
                price_elem = card.find_element(By.CSS_SELECTOR, ".fare-price")
                price_text = price_elem.text.replace("€", "").replace(",", ".").strip()
                price = float(price_text)
                if price > 0:
                    prices.append(price + 3.0)
            except:
                continue

    except TimeoutException as err:
        print(f"Timeout {origen} -> {destination} : {err}")
    except Exception as e:
        print(f"Erreur inattendue {origen} -> {destination} : {e}")

    if not prices:
        print("⚠️ Extraction vide — aucun vol détecté.")
        return []

    print(f"Extraction réussie : {len(prices)} vols trouvés.")
    return prices
