"""
Scraper de prix Air Corsica via l'API officielle Google Flights (SerpApi)
============================================================================

Remplace l'ancienne approche par navigateur (Playwright/Selenium/OCR) qui
contournait les protections anti-bot d'Air Corsica (Imperva). Ici, on
interroge Google Flights via SerpApi, un service qui republie ces données
via un accès légal. Aucune protection à contourner, aucune IP résidentielle
requise, ça tourne sur GitHub Actions sans problème.

Principe : chaque appel renvoie un prix le plus bas, une fourchette
"typique" et un niveau de prix (price_insights) pour une date donnée.
On interroge 5 horizons par liaison (J+7, J+30, J+60, J+90, J+120) pour
obtenir une vraie courbe plutôt que deux points isolés. Soit 46 routes x 5
horizons = 230 requêtes par run, qui tient dans le quota gratuit SerpApi
(250/mois) à raison d'un run complet par mois.

Installation :
    pip install requests

Configuration :
    export SERPAPI_KEY="votre_cle_api"
    # Clé gratuite sur https://serpapi.com (plan gratuit : 100 requêtes/mois)

Usage :
    python scraper_aircorsica_api.py                  # toutes les routes, J+7 à J+120 (5 points)
    python scraper_aircorsica_api.py --test AJA MRS    # une seule route, pour tester
"""

import os
import csv
import time
import argparse
import requests
from datetime import date, timedelta

# --- Configuration -----------------------------------------------------

API_KEY = os.environ.get("SERPAPI_KEY")
API_URL = "https://serpapi.com/search"

# Horizons de suivi (en jours), du court au long terme.
# 5 points x 46 routes = 230 requêtes/run, dans le quota gratuit (250/mois).
HORIZONS = {"J7": 7, "J30": 30, "J60": 60, "J90": 90, "J120": 120}

# Liste des 46 liaisons à suivre : (origine, destination) en code IATA.
# 4 aéroports corses (AJA, BIA, FSC, CLY) vers 6 aéroports continentaux,
# dans les deux sens. CLY n'a pas de liaison vers TLS (23 paires -> 46 routes).
corsica_destinations = {
    "AJA": ["ORY", "CDG", "MRS", "NCE", "LYS", "TLS"],
    "BIA": ["ORY", "CDG", "MRS", "NCE", "LYS", "TLS"],
    "FSC": ["ORY", "CDG", "MRS", "NCE", "LYS", "TLS"],
    "CLY": ["ORY", "CDG", "MRS", "NCE", "LYS"],
}

ROUTES = []
for cor, main_list in corsica_destinations.items():
    for main in main_list:
        ROUTES.append((cor, main))   # Corse -> Continent
        ROUTES.append((main, cor))   # Continent -> Corse

OUTPUT_DIR = "routes_aircorsica"
MASTER_FILE = "historique_global_france.csv"

DELAY_BETWEEN_CALLS = 2  # secondes, pour rester raisonnable vis-à-vis de l'API


# --- Appel API -----------------------------------------------------------

# Traduction des niveaux de prix renvoyés par l'API (anglais -> français)
NIVEAUX_PRIX = {"low": "bas", "typical": "normal", "high": "élevé"}


def query_price(origin: str, dest: str, target_date: str):
    """Interroge SerpApi pour une liaison et une date données (aller simple)."""
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": dest,
        "outbound_date": target_date,
        "type": "2",  # aller simple
        "currency": "EUR",
        "hl": "fr",
        "api_key": API_KEY,
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("search_metadata", {}).get("status") != "Success":
        print(f"  ! Échec pour {origin}->{dest} le {target_date}: "
              f"{data.get('error', 'raison inconnue')}")
        return None

    insights = data.get("price_insights", {})
    flights = data.get("best_flights") or data.get("other_flights") or []
    prices = [f.get("price") for f in flights if f.get("price")]
    cheapest = min(prices) if prices else None

    typical_range = insights.get("typical_price_range") or [None, None]
    niveau_en = insights.get("price_level", "")

    return {
        "lowest_price": insights.get("lowest_price", cheapest),
        "price_level": NIVEAUX_PRIX.get(niveau_en, niveau_en),
        "typical_min": typical_range[0],
        "typical_max": typical_range[1],
    }


# --- Écriture CSV --------------------------------------------------------

def append_row(filepath: str, row: dict, fieldnames: list) -> None:
    """Ajoute une ligne en tête de fichier (le plus récent en premier)."""
    existing_rows = []
    if os.path.exists(filepath):
        with open(filepath, newline="", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f, delimiter=";"))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerow(row)
        writer.writerows(existing_rows)


# --- Boucle principale -----------------------------------------------------

def main(test_routes=None):
    if not API_KEY:
        raise SystemExit("Erreur : variable d'environnement SERPAPI_KEY manquante.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    routes = ROUTES
    if test_routes:
        routes = [r for r in ROUTES if r[0] in test_routes or r[1] in test_routes]
        if not routes and len(test_routes) >= 2:
            routes = [(test_routes[0], test_routes[1])]

    scrape_date = date.today().isoformat()
    fieldnames = ["date_maj", "origin", "dest", "horizon", "date_cible",
                  "lowest_price", "price_level", "typical_min", "typical_max", "devise"]

    total = len(routes) * len(HORIZONS)
    count = 0

    for origin, dest in routes:
        route_file = os.path.join(OUTPUT_DIR, f"{origin}_{dest}.csv")

        for horizon_label, jours in HORIZONS.items():
            count += 1
            target_date = (date.today() + timedelta(days=jours)).isoformat()
            print(f"[{count}/{total}] {origin} -> {dest} ({horizon_label}, {target_date})")

            result = query_price(origin, dest, target_date)
            if result is None:
                time.sleep(DELAY_BETWEEN_CALLS)
                continue

            row = {
                "date_maj": scrape_date,
                "origin": origin,
                "dest": dest,
                "horizon": horizon_label,
                "date_cible": target_date,
                "lowest_price": result["lowest_price"],
                "price_level": result["price_level"],
                "typical_min": result["typical_min"],
                "typical_max": result["typical_max"],
                "devise": "EUR",
            }

            append_row(route_file, row, fieldnames)
            append_row(os.path.join(OUTPUT_DIR, os.pardir, MASTER_FILE), row, fieldnames)

            time.sleep(DELAY_BETWEEN_CALLS)

    print(f"\nTerminé. {count} requêtes effectuées ce mois-ci "
          f"(quota gratuit SerpApi : 250/mois — {250 - count} restantes ce mois-ci).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", nargs="+",
                         help="Codes IATA pour tester une seule route, ex: --test AJA MRS")
    args = parser.parse_args()
    main(test_routes=args.test)
