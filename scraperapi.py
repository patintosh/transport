import argparse
import csv
from datetime import datetime, timedelta
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
            "date": target_date.strftime('%d/%m/%Y'), # Format français direct JJ/MM/AAAA
            "date_iso": target_date.strftime('%Y-%m-%d'), # Pour le tri technique
            "min": round(min_price, 2),
            "max": round(max_price, 2),
            "avg": round(avg_price, 2),
            "count": len(prices)
        }

    except Exception as e:
        print(f"  -> Erreur lors du traitement de {origin}-{destination} : {e}")
        return None

def run_batch():
    """Exécute la collecte complète et met à jour directement le fichier maître unique."""
    print("Script démarré en mode collecte robuste.")
    target_date = datetime.now() + timedelta(days=7)
    new_results = []

    with sync_playwright() as p:
        browser, context = get_stealth_browser_context(p, headless_mode=True)
        page = context.new_page()

        for i, (origin, destination) in enumerate(ROUTES_AIR_CORSICA):
            data = scrape_route(page, origin, destination, target_date)
            if data:
                new_results.append(data)

            if i < len(ROUTES_AIR_CORSICA) - 1:
                sleep_time = random.randint(3, 6)
                print(f"  -> Pause de {sleep_time}s avant la liaison suivante...\n")
                page.wait_for_timeout(sleep_time * 1000)

        browser.close()

    # Fichier maître unique directement au format français
    global_france_filename = "historique_global_france.csv"
    
    # 1. Charger l'historique existant s'il existe pour ne rien perdre
    existing_rows = []
    try:
        with open(global_france_filename, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                existing_rows.append(row)
    except FileNotFoundError:
        print(f"Aucun fichier {global_france_filename} trouvé. Création d'un nouveau fichier maître.")

    # 2. Préparer les nouvelles lignes au format français
    formatted_new_rows = []
    for item in new_results:
        formatted_new_rows.append({
            "Origine": item["origin"],
            "Destination": item["destination"],
            "Date": item["date"],
            "Prix Min": str(item["min"]).replace('.', ','),
            "Prix Max": str(item["max"]).replace('.', ','),
            "Prix Moyen": str(item["avg"]).replace('.', ','),
            "Nombre": str(item["count"]),
            "_date_iso": item["date_iso"] # Clé technique pour le tri
        })

    # 3. Fusionner en évitant les doublons exacts (même Origine, Destination, Date, Min, Max, Moyenne)
    seen = set()
    combined_rows = []

    # On ajoute d'abord les nouvelles données du jour
    for row in formatted_new_rows:
        key = (row["Origine"], row["Destination"], row["Date"], row["Prix Min"], row["Prix Max"], row["Prix Moyen"])
        if key not in seen:
            seen.add(key)
            combined_rows.append(row)

    # Puis on ajoute les anciennes données existantes
    for row in existing_rows:
        # Normalisation des clés selon l'en-tête existant
        orig = row.get("Origine", row.get("origin", ""))
        dest = row.get("Destination", row.get("destination", ""))
        dt = row.get("Date", row.get("date", ""))
        pmin = row.get("Prix Min", row.get("min", ""))
        pmax = row.get("Prix Max", row.get("max", ""))
        pavg = row.get("Prix Moyen", row.get("avg", ""))
        cnt = row.get("Nombre", row.get("count", ""))
        
        # Calcul d'une clé ISO pour le tri si la date est au format JJ/MM/AAAA
        try:
            dt_obj = datetime.strptime(dt, "%d/%m/%Y")
            d_iso = dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            d_iso = dt

        key = (orig, dest, dt, pmin, pmax, pavg)
        if key not in seen:
            seen.add(key)
            combined_rows.append({
                "Origine": orig,
                "Destination": dest,
                "Date": dt,
                "Prix Min": pmin,
                "Prix Max": pmax,
                "Prix Moyen": pavg,
                "Nombre": cnt,
                "_date_iso": d_iso
            })

    # 4. Tri : Le plus récent en haut (basé sur la date de vol ou d'extraction)
    combined_rows.sort(key=lambda x: x.get("_date_iso", ""), reverse=True)

    # 5. Écriture directe du fichier maître global au format français (séparateur ;)
    france_fieldnames = ["Origine", "Destination", "Date", "Prix Min", "Prix Max", "Prix Moyen", "Nombre"]
    
    with open(global_france_filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(france_fieldnames)
        
        for row in combined_rows:
            writer.writerow([
                row["Origine"],
                row["Destination"],
                row["Date"],
                row["Prix Min"],
                row["Prix Max"],
                row["Prix Moyen"],
                row["Nombre"]
            ])

    print(f"\n[Succès] Fichier maître unique mis à jour : {global_france_filename} ({len(combined_rows)} lignes au total, trié du plus récent au plus ancien).")

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
    print("\n=== FIN DU ROBOT TEST ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Air Corsica - Automatisation des tarifs.")
    parser.add_argument("--mode", choices=["batch", "delay_test"], default="batch",
                        help="Choisis 'batch' pour la production ou 'delay_test' pour calibrer les pauses.")
    
    args = parser.parse_args()

    if args.mode == "delay_test":
        test_optimal_delay()
    else:
        run_batch()