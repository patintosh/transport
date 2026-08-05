import asyncio
from datetime import datetime, timedelta
import os
import pandas as pd
from playwright.async_api import async_playwright

# Configuration du fichier de sortie dédié J+90
CSV_FILE = "historique_j90_france.csv"

# Définition des liaisons (identiques à votre script principal)
ROUTES = [
    {"origin": "AJA", "destination": "ORY"},
    {"origin": "AJA", "destination": "CDG"},
    {"origin": "AJA", "destination": "MRS"},
    {"origin": "AJA", "destination": "NCE"},
    {"origin": "AJA", "destination": "LYS"},
    {"origin": "BIA", "destination": "ORY"},
    {"origin": "BIA", "destination": "CDG"},
    {"origin": "BIA", "destination": "MRS"},
    {"origin": "BIA", "destination": "NCE"},
    {"origin": "BIA", "destination": "LYS"},
    {"origin": "CLY", "destination": "ORY"},
    {"origin": "CLY", "destination": "CDG"},
    {"origin": "CLY", "destination": "MRS"},
    {"origin": "CLY", "destination": "NCE"},
    {"origin": "FSC", "destination": "ORY"},
    {"origin": "FSC", "destination": "CDG"},
    {"origin": "FSC", "destination": "MRS"},
    {"origin": "FSC", "destination": "NCE"},
]


async def scrape_air_corsica():
  # Calcul de la date cible à J+90
  target_date = datetime.now() + timedelta(days=90)
  date_str = target_date.strftime("%d/%m/%Y")
  print(f"--- Lancement du scraper J+90 pour la date : {date_str} ---")

  new_records = []

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()

    for route in ROUTES:
      origin = route["origin"]
      destination = route["destination"]

      # URL de recherche Air Corsica (à adapter selon votre structure exacte d'URL validée dans scraperapi.py)
      url = f"https://www.aircorsica.com/flight/search?origin={origin}&destination={destination}&date={date_str}"

      try:
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(
            3000
        )  # Pause pour laisser charger les prix

        # Extraction des prix (exemple basé sur la structure de votre sélecteur habituel)
        # Assurez-vous d'ajuster le sélecteur si besoin en fonction de votre scraper principal
        prices = await page.eval_on_selector_all(
            ".price-class",
            "(elements) => elements.map(el => parseFloat(el.innerText.replace('€', '').replace(',', '.').trim()))",
        )

        if prices:
          prix_min = min(prices)
          prix_max = max(prices)
          prix_moyen = sum(prices) / len(prices)
          nombre = len(prices)

          # Formatage avec virgule pour le format français
          new_records.append({
              "Origine": origin,
              "Destination": destination,
              "Date": date_str,
              "Prix Min": f"{prix_min:.2f}".replace(".", ","),
              "Prix Max": f"{prix_max:.2f}".replace(".", ","),
              "Prix Moyen": f"{prix_moyen:.2f}".replace(".", ","),
              "Nombre": nombre,
          })
          print(
              f"[{origin} -> {destination}] Succès : Min={prix_min}€,"
              f" Max={prix_max}€"
          )
        else:
          print(
              f"[{origin} -> {destination}] Aucun vol trouvé pour cette date."
          )

      except Exception as e:
        print(f"[{origin} -> {destination}] Erreur lors du scraping : {e}")

      # Petite pause entre chaque liaison pour éviter d'surcharger
      await asyncio.sleep(2)

    await browser.close()

  # Mise à jour et fusion avec le fichier maître J+90
  if new_records:
    df_new = pd.DataFrame(new_records)

    if os.path.exists(CSV_FILE):
      df_existing = pd.read_csv(CSV_FILE, sep=";", dtype=str)
      df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
      df_combined = df_new

    # Nettoyage des doublons éventuels et tri chronologique
    df_combined.drop_duplicates(
        subset=["Origine", "Destination", "Date"], keep="last", inplace=True
    )

    # Tri par date et liaisons
    df_combined["_temp_date"] = pd.to_datetime(
        df_combined["Date"], format="%d/%m/%Y"
    )
    df_combined.sort_values(
        by=["_temp_date", "Origine", "Destination"], ascending=[True, True, True], inplace=True
    )
    df_combined.drop(columns=["_temp_date"], inplace=True)

    # Sauvegarde au format français (séparateur point-virgule)
    df_combined.to_csv(CSV_FILE, sep=";", index=False, encoding="utf-8-sig")
    print(
        f"\n[Succès] Fichier {CSV_FILE} mis à jour avec {len(new_records)}"
        " nouvelles lignes."
    )
  else:
    print("\nAucune donnée récupérée lors de ce run.")


if __name__ == "__main__":
  asyncio.run(scrape_air_corsica())