import csv
from datetime import datetime, timedelta
from selenium import webdriver
from scraper_aircorsica import scrape_route

# --- ROUTES À SCRAPER ---
ROUTES = [
    ("ORY", "AJA"),
    ("ORY", "BIA"),
    ("ORY", "CLY"),
    ("ORY", "FSC"),
]

# --- DATE J+7 ---
target_date = datetime.today() + timedelta(days=7)
target_date_str = target_date.strftime("%Y-%m-%d")
target_date_display = target_date.strftime("%d/%m/%Y")

# --- FICHIER DE SORTIE ---
OUTPUT_FILE = "vols_aircorsica.csv"

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def main():
    all_rows = []

    for origen, destination in ROUTES:
        print(f"Scraping {origen} → {destination} pour le {target_date_display}")

        driver = create_driver()
        prices = scrape_route(driver, origen, destination, target_date_str, target_date_display)
        driver.quit()

        if not prices:
            print(f"⚠️ Aucun prix trouvé pour {origen} → {destination}, ligne ignorée.")
            continue

        row = {
            "Date_Capture": datetime.today().strftime("%Y-%m-%d"),
            "Départ": origen,
            "Arrivée": destination,
            "Date vol": target_date_display,
            "Prix": prices
        }
        all_rows.append(row)

    if not all_rows:
        print("⚠️ Aucune donnée à écrire — extraction vide.")
        return

    print(f"Écriture dans {OUTPUT_FILE}…")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Date_Capture", "Départ", "Arrivée", "Date vol", "Prix"])
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print("Scraping terminé.")

if __name__ == "__main__":
    main()
