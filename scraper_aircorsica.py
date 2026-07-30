import requests
import time
import json
from statistics import mean
import datetime
import csv
import os

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
    try:
        price_list = data["priceByBound"][0]["priceList"]
        prices = [p["amount"] for p in price_list if "amount" in p]
        return prices
    except Exception:
        return []

def compute_stats(prices):
    if not prices:
        return None
    return {
        "min": min(prices),
        "max": max(prices),
        "mean": mean(prices)
    }

def append_to_global_csv(rows, filename="résultats_aircorsica.csv"):
    existing = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing = list(reader)

    all_rows = existing + rows

    all_rows_sorted = sorted(
        all_rows,
        key=lambda r: (r["scrape_date"], r["flight_date"], r["origin"], r["dest"])
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scrape_date", "flight_date", "origin", "dest", "min", "max", "mean"]
        )
        writer.writeheader()
        writer.writerows(all_rows_sorted)

def append_to_route_csv(rows, origin, dest):
    os.makedirs("routes_aircorsica", exist_ok=True)
    filename = f"routes_aircorsica/{origin}_{dest}.csv"

    existing = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing = list(reader)

    all_rows = existing + rows

    all_rows_sorted = sorted(
        all_rows,
        key=lambda r: (r["scrape_date"], r["flight_date"])
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scrape_date", "flight_date", "min", "max", "mean"]
        )
        writer.writeheader()
        writer.writerows(all_rows_sorted)

if __name__ == "__main__":
    session = create_session()

    scrape_date = datetime.datetime.now().strftime("%Y%m%d")
    flight_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y%m%d0000")

    global_rows = []

    for origin, dest in get_routes(session):
        data = flex_pricer(session, origin, dest, flight_date)
        prices = extract_prices(data)
        stats = compute_stats(prices)
        if stats:
            row = {
                "scrape_date": scrape_date,
                "flight_date": flight_date,
                "origin": origin,
                "dest": dest,
                "min": stats["min"],
                "max": stats["max"],
                "mean": stats["mean"]
            }
            global_rows.append(row)
            append_to_route_csv([row], origin, dest)

    append_to_global_csv(global_rows)
    print(f"{len(global_rows)} lignes ajoutées à résultats_aircorsica.csv")
