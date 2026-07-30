import requests

def scrape_route(origen, destination, target_date_str):
    url = "https://book.aircorsica.com/api/search"

    params = {
        "origin": origen,
        "destination": destination,
        "date": target_date_str,
        "adt": 1,
        "chd": 0,
        "inf": 0
    }

    r = requests.get(url, params=params, timeout=30)
    data = r.json()

    prices = []

    for flight in data.get("flights", []):
        price = flight.get("price")
        if price:
            prices.append(price + 3.0)

    return prices
