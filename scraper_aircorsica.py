import requests
import time
import json
from statistics import mean

BASE = "https://book.aircorsica.com/plnext/AirCorsicaDX"

def create_session():
    s = requests.Session()
    s.get(BASE + "/")
    return s

def get_routes(session):
    url = BASE + "/resources/json/markets.json"
    r = session.get(url)
    data = r.json()
    routes = []

    for market in data.get("markets", []):
        dep = market.get("departure")
        arrs = market.get("arrival", [])
        for arr in arrs:
            routes.append((dep, arr))

    return routes

def flex_pricer(session, origin, dest, date_str):
    jsessionid = session.cookies.get("JSESSIONID")
    url = f"{BASE}/FlexPricerAvailabilityDispatcherPui.action;jsessionid={jsessionid}"

    payload = {
        "COUNTRY_SITE": "GB",
        "DATE_RANGE_QUALIFIER_2": "C",
        "BOOKING_FLOW": "REVENUE",
        "INITIAL_TRIP_TYPE": "O",
        "DATE_RANGE_QUALIFIER_1": "C",
        "PAGE_TICKET": "1",
        "STATE": "REGULAR",
        "B_ANY_TIME_1": "TRUE",
        "B_ANY_TIME_2": "TRUE",
        "TRIP_FLOW": "YES",
        "DISPLAY_TYPE": "1",
        "LANGUAGE": "FR",
        "ARRANGE_BY": "D",
        "COMMERCIAL_FARE_FAMILY_1": "CFFYJV1",
        "SITE": "BDEQBNEW",
        "isOverrideAction": "false",
        "PLTG_IS_UPSELL": "true",
        "E_LOCATION_1": dest,
        "E_LOCATION_2": origin,
        "_t": int(time.time()),
        "TRIP_TYPE": "O",
        "PRICING_TYPE": "O",
        "OFFICE_ID": "AJAXK08AB",
        "HAS_INFANT_1": "FALSE",
        "FORCE_CALENDAR": "FALSE",
        "DATE_RANGE_VALUE_1": "0",
        "DATE_RANGE_VALUE_2": "0",
        "B_DATE_1": date_str,
        "B_DATE_2": date_str,
        "TRAVELLER_TYPE_1": "ADT",
        "DATA_TYPE": "json"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Accept": "*/*",
        "Referer": BASE + "/",
        "User-Agent": "Mozilla/5.0"
    }

    r = session.post(url, data=payload, headers=headers)
    return r.json()

def extract_prices(data):
    """Extrait tous les prix disponibles dans la réponse FlexPricer."""
    try:
        price_list = data["priceByBound"][0]["priceList"]
        prices = [p["amount"] for p in price_list if "amount" in p]
        return prices
    except Exception:
        return []

def compute_stats(prices):
    """Retourne min, max, moyenne."""
    if not prices:
        return None
    return {
        "min": min(prices),
        "max": max(prices),
        "mean": mean(prices)
    }

def scrape_all_routes(date_str):
    """Scrape toutes les routes Air Corsica pour une date donnée."""
    session = create_session()
    routes = get_routes(session)

    results = {}

    for origin, dest in routes:
        try:
            data = flex_pricer(session, origin, dest, date_str)
            prices = extract_prices(data)
            stats = compute_stats(prices)
            results[(origin, dest)] = stats
        except Exception as e:
            results[(origin, dest)] = {"error": str(e)}

    return results

if __name__ == "__main__":
    # Exemple : J+7
    import datetime
    target_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y%m%d0000")
    results = scrape_all_routes(target_date)
    print(json.dumps(results, indent=2))
