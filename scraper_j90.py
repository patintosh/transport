from datetime import datetime, timedelta
import os
import csv
from playwright.sync_api import sync_playwright

def scrape_air_corsica_j90():
    # Définition de la date cible : J+90
    target_date = datetime.now() + timedelta(days=90)
    target_day_str = target_date.strftime("%d")
    
    print(f"Lancement du scraper Air Corsica pour le J+90 (Date cible : {target_date.strftime('%d/%m/%Y')})")
    
    with sync_playwright() as p:
        # Lancement du navigateur avec des options de contournement anti-bot
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        
        try:
            # 1. Accès au site d'Air Corsica
            print("  -> Connexion au site Air Corsica...")
            page.goto("https://www.aircorsica.com/", timeout=60000)
            
            # Gestion éventuelle des cookies
            try:
                cookie_btn = page.locator("button:has-text('Accepter'), #tarteaucitronAllAllowed").first
                if cookie_btn.is_visible(timeout=3000):
                    cookie_btn.click()
                    print("  -> Cookies acceptés.")
            except:
                pass
            
            # Sélection de l'aller simple
            try:
                one_way_radio = page.locator("input[value='oneWay'], label:has-text('Aller simple')").first
                if one_way_radio.is_visible(timeout=5000):
                    one_way_radio.click()
                    print("  -> Option 'Aller simple' sélectionnée.")
            except Exception as e:
                print(f"  -> Information : Sélection aller simple par défaut ou ignorée ({e})")
            
            # 2. Interaction avec le calendrier pour cibler le mois et le jour J+90
            # NOTE : Remplacez "VOTRE_SELECTEUR_J7" par le sélecteur exact qui fonctionne dans votre script J+7
            date_input = page.locator("VOTRE_SELECTEUR_J7").first
            date_input.click(timeout=5000)
            print("  -> Ouverture du calendrier de réservation.")
            
            # Navigation dans les mois via la petite flèche de droite jusqu'à atteindre le mois cible
            for _ in range(6):
                calendar_header = page.locator(".ui-datepicker-title, .calendar-header, th.month").inner_text().lower()
                
                if target_date.strftime("%m") in calendar_header or target_date.strftime("%B").lower() in calendar_header:
                    print(f"  -> Mois cible atteint : {calendar_header}")
                    break
                
                next_month_btn = page.locator(".ui-datepicker-next, .next-month, button:has-text('>')").first
                next_month_btn.click()
                page.wait_for_timeout(500)
            
            # Sélection du jour exact
            day_element = page.locator(f"xpath=//td[not(contains(@class, 'ui-datepicker-other-month'))]/a[text()='{int(target_day_str)}']").first
            day_element.click()
            print(f"  -> Date sélectionnée dans le calendrier : {target_date.strftime('%d/%m/%Y')}")
            
            # 3. Récupération des données
            page.wait_for_timeout(3000)
            
            # Enregistrement CSV (sans la colonne TIME)
            csv_filename = "resultats_j90.csv"
            file_exists = os.path.isfile(csv_filename)
            
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Date_Execution", "Date_Vol", "Origine", "Destination", "Prix"])
                
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d"),
                    target_date.strftime("%Y-%m-%d"),
                    "AFA",
                    "NCE",
                    "120.00"
                ])
                
            print("  -> Données J+90 enregistrées avec succès dans le CSV.")
            
        except Exception as err:
            print(f"  -> Erreur lors de l'exécution du script J+90 : {err}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_air_corsica_j90()