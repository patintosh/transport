from playwright.sync_api import sync_playwright
import time

def scrape_air_corsica():
    with sync_playwright() as p:
        # Lancement du navigateur (headless=True pour GitHub Actions, False pour le debug local)
        browser = p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Création d'un contexte avec un User-Agent réaliste pour limiter les blocages anti-bot
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        print("Accès au site d'Air Corsica...")
        page.goto("https://www.aircorsica.com/", timeout=60000)

        # 1. Gestion du bandeau de cookies
        try:
            cookie_button = page.locator("#onetrust-accept-btn-handler")
            if cookie_button.is_visible(timeout=5000):
                cookie_button.click()
                print("Bandeau de cookies fermé.")
        except Exception:
            print("Aucun bandeau de cookies détecté ou déjà accepté.")

        # 2. Sélection du type de parcours : "Aller simple"
        print("Sélection de l'option 'Aller simple'...")
        # On cible le label visible pour éviter les blocages de géométrie de Playwright sur l'input masqué
        page.locator("label[for='edit-booking-flight-v2-travel-type-o']").click()

        # 3. Sélection de l'aéroport de départ (Exemple : Ajaccio - AJA)
        print("Sélection de l'aéroport de départ...")
        page.select_option("#edit-booking-flight-v2-from", "AJA")

        # 4. Attente et sélection de l'aéroport d'arrivée (Exemple : Paris Orly - ORY)
        print("Attente de l'activation du champ d'arrivée...")
        page.wait_for_selector("#edit-booking-flight-v2-to:not([disabled])", timeout=10000)
        
        print("Sélection de l'aéroport d'arrivée...")
        page.select_option("#edit-booking-flight-v2-to", "ORY")

        # Petite pause pour laisser le temps au formulaire de se mettre à jour
        time.sleep(2)

        print("Formulaire initial renseigné avec succès !")
        
        # Vous pouvez ajouter ici la suite pour la sélection des dates et la récupération des prix
        
        browser.close()

if __name__ == "__main__":
    scrape_air_corsica()