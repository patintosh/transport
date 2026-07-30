import pandas as pd
from datetime import datetime, timedelta
from scraper_aircorsica import scrape_route

def main():
    routes = [
        ("ORY", "AJA"),
        ("ORY", "BIA"),
        ("ORY", "CLY"),
        ("ORY", "FSC")
    ]

    target_date = datetime.now() + timedelta(days=7)
    target_date_str = target_date.strftime("%Y-%m-%d")

    rows = []

    for origen, destination in routes:
        print(f"Scraping {origen} → {destination} pour le {target_date_str}")

        prices = scrape_route(origen, destination, target_date_str)

        if prices:
            for p in prices:
                rows.append([origen, destination, target_date_str, p])
        else:
            print(f"⚠️ Aucun prix trouvé pour {origen} → {destination}, ligne ignorée.")

    if rows:
        df = pd.DataFrame(rows, columns=["origine", "destination", "date", "prix"])
        df.to_csv("vols_aircorsica.csv", index=False)
        print("CSV généré : vols_aircorsica.csv")
    else:
        print("⚠️ Aucune donnée à écrire — extraction vide.")

if __name__ == "__main__":
    main()
