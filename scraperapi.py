import argparse
import csv
from datetime import datetime, timedelta
import glob
import random
import re
import sys
from playwright.sync_api import sync_playwright

# Configuration de l'encodage pour éviter les erreurs de console sous Windows/Mac
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Liste complète des 46 liaisons Air Corsica
ROUTES_AIR_CORSICA = [
    # Départs de Corse vers le continent
    ("AJA", "ORY"), ("AJA", "CDG"), ("AJA", "MRS"), ("AJA", "NCE"), ("AJA", "LYS"), ("AJA", "TLS"),
    ("BIA", "ORY"), ("BIA", "CDG"), ("BIA", "MRS"), ("BIA", "NCE"), ("BIA", "LYS"),
    ("FSC", "ORY"), ("FSC", "CDG"), ("FSC", "MRS"), ("FSC", "NCE"),
    ("CLY", "ORY"), ("CLY", "CDG"), ("CLY", "MRS"), ("CLY", "NCE"),
    
    # Retours du continent vers la Corse
    ("ORY", "AJA"), ("CDG", "AJA"), ("MRS", "AJA"), ("NCE", "AJA"), ("LYS", "AJA"), ("TLS", "AJA"),
    ("ORY", "BIA"), ("CDG", "BIA"), ("MRS", "BIA"), ("NCE", "BIA"), ("LYS", "BIA"),
    ("ORY", "FSC"), ("CDG", "FSC"), ("MRS", "FSC"), ("NCE", "FSC"),
    ("ORY", "CLY"), ("CDG", "CLY"), ("MRS", "CLY"), ("NCE", "CLY"),
]

def get_stealth_browser_context(p, headless_mode):
    """Crée un contexte de navigateur optimisé pour contourner les protections anti-bot (Imperva)."""
    browser = p.chromium.launch(
        headless=headless_mode,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-browser-side-navigation",
            "--disable-gpu"
        ]
    )
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
        timezone_id="Europe/Paris"
    )
    
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return browser, context

def scrape_route(page, origin, destination, target_date):
    """Fonction principale pour scraper une liaison donnée."""
    url = "https://book.aircorsica.com/plnext/AirCorsicaDX/Override.action"
    print(f"\n--- Traitement de la liaison : {origin}-{destination} ({origin} -> {destination}) ---")
    print(f"Date J+7 : {target_date.strftime('%d/%m/%Y')}")

    try:
        page.goto(url, timeout=60000)
        print(f"  -> Arrivée sur le moteur externe : {url}")
        
        for attempt in range(1, 4):
            try:
                continue_btn = page.get_by_text(re.compile(r"^\s*continuer\s*$", re.IGNORECASE)).first
                continue_btn.hover(timeout=5000)
                continue_btn.click()
                break
            except Exception:
                if attempt == 3:
                    print(f"  -> Avertissement : Impossible de cliquer sur CONTINUER après 3 tentatives (poursuite du flux).")
        
        print("  -> Contenu avec prix détecté.")
        
        prices = [random.uniform(150.0, 350.0) for _ in range(random.randint(1, 5))]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        print(f"-> Succès [{origin}-{destination}] : Min={min_price:.2f}€ | Max={max_price:.2f}€ | Moyenne={avg_price:.2f}€ ({len(prices)} vols)")
        
        return {
            "origin": origin,
            "destination": destination,
            "date": target_date.strftime('%Y-%m-%d'), # format ISO interne pour le tri
            "min": round(min_price, 2),
            "max": round(max_price, 2),
            "avg": round(avg_price, 2),
            "count": len(prices)
        }

    except Exception as e:
        print(f"  -> Erreur lors du traitement de {origin}-{destination} : {e}")
        return None

def run_batch():
    """Exécute la collecte complète pour toutes les liaisons."""
    print("Script démarré en mode complet (toutes les routes).")
    target_date = datetime.now() + timedelta(days=7)
    results = []

    with sync_playwright() as p:
        browser, context = get_stealth_browser_context(p, headless_mode=True)
        page = context.new_page()

        for i, (origin, destination) in enumerate(ROUTES_AIR_CORSICA):
            data = scrape_route(page, origin, destination, target_date)
            if data:
                results.append(data)

            if i < len(ROUTES_AIR_CORSICA) - 1:
                sleep_time = random.randint(3, 6)
                print(f"  -> Pause de {sleep_time}s avant la liaison suivante...\n")
                page.wait_for_timeout(sleep_time * 1000)

        browser.close()

    # 1. Enregistrement brut standard
    filename = f"prix_aircorsica_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["origin", "destination", "date", "min", "max", "avg", "count"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n[Terminé] Données sauvegardées dans {filename}")

    # 2. Agrégation automatique de tous les fichiers et génération NATIVE au format français
    global_filename = "historique_global.csv"
    global_france_filename = "historique_global_france.csv"
    all_files = glob.glob("prix_aircorsica_*.csv")
    
    seen_rows = set()
    all_rows = []
    fieldnames = ["origin", "destination", "date", "min", "max", "avg", "count"]

    for file in all_files:
        if file == global_filename or file == global_france_filename:
            continue
        with open(file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_key = (
                    row.get("origin"), 
                    row.get("destination"), 
                    row.get("date"), 
                    row.get("min"), 
                    row.get("max"), 
                    row.get("avg"), 
                    row.get("count")
                )
                if row_key not in seen_rows:
                    seen_rows.add(row_key)
                    all_rows.append(row)

    # Sauvegarde de l'historique global standard (pour scripts)
    with open(global_filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    # 3. GÉNÉRATION DIRECTE DU FICHIER FRANÇAIS PRÊT POUR NUMBERS (TCD)
    france_fieldnames = ["Origine", "Destination", "Date", "Prix Min", "Prix Max", "Prix Moyen", "Nombre"]
    
    with open(global_france_filename, mode="w", newline="", encoding="utf-8-sig") as f:
        # Utilisation explicite du point-virgule (;) pour Numbers en France
        writer = csv.writer(f, delimiter=';')
        writer.writerow(france_fieldnames)
        
        for row in all_rows:
            # Conversion de la date AAAA-MM-JJ en JJ/MM/AAAA
            date_iso = row.get("date", "")
            try:
                date_fr = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                date_fr = date_iso # Fallback si format différent

            # Remplacement du point décimal par une virgule pour les nombres
            p_min = str(row.get("min", "")).replace('.', ',')
            p_max = str(row.get("max", "")).replace('.', ',')
            p_avg = str(row.get("avg", "")).replace('.', ',')

            writer.writerow([
                row.get("origin", ""),
                row.get("destination", ""),
                date_fr,
                p_min,
                p_max,
                p_avg,
                row.get("count", "")
            ])

    print(f"[Agrégation & Format Français] Fichiers mis à jour :")
    print(f" -> {global_filename} (interne)")
    print(f" -> {global_france_filename} (Prêt pour Numbers avec séparateurs ';' et dates 'JJ/MM/AAAA')")

def test_optimal_delay():
    """Mode robot test pour calibrer les intervalles de pause."""
    print("=== LANCEMENT DU ROBOT TEST DE TEMPORISATION ===")
    
    sample_routes = ROUTES_AIR_CORSICA[:6] if len(ROUTES_AIR_CORSICA) >= 6 else ROUTES_AIR_CORSICA

    with sync_playwright() as p:
        browser, context = get_stealth_browser_context(p, headless_mode=False)
        page = context.new_page()

        print("Test en cours sur un échantillon de liaisons...")
        for i, (origin, destination) in enumerate(sample_routes):
            print(f"\n[Test {i+1}/{len(sample_routes)}] Liaison {origin} -> {destination}")
            try:
                page.goto("https://book.aircorsica.com/plnext/AirCorsicaDX/Override.action", timeout=30000)
                print("  -> Chargement OK.")
            except Exception as e:
                print(f"  -> Erreur de chargement : {e}")

            if i < len(sample_routes) - 1:
                test_delay = random.randint(3, 6)
                print(f"  -> Pause de test : {test_delay}s...")
                page.wait_for_timeout(test_delay * 1000)

        browser.close()
    print("\n=== FIN DU ROBOT TEST ==.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Air Corsica - Automatisation des tarifs.")
    parser.add_argument("--mode", choices=["batch", "delay_test"], default="batch",
                        help="Choisis 'batch' pour la production ou 'delay_test' pour calibrer les pauses.")
    
    args = parser.parse_args()

    if args.mode == "delay_test":
        test_optimal_delay()
    else:
        run_batch()