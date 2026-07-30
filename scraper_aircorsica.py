from playwright.sync_api import sync_playwright

def scrape_route(origen, destination, target_date_str):
    prices = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Page d'accueil
        page.goto("https://book.aircorsica.com/", timeout=60000)

        # Cookies
        try:
            page.click("#onetrust-accept-btn-handler", timeout=5000)
        except:
            pass

        # Origine
        page.fill("#origin-input", origen)
        page.click("ul#origin-list li", timeout=10000)

        # Destination
        page.fill("#destination-input", destination)
        page.click("ul#destination-list li", timeout=10000)

        # Recherche
        page.click("#search-button", timeout=15000)

        # Date
        page.click(f"td[data-date='{target_date_str}']", timeout=15000)

        # Continuer
        page.click("#continue-button", timeout=15000)

        # Attendre les vols
        page.wait_for_selector("div.flight-card", timeout=30000)

        # Extraction
        cards = page.query_selector_all("div.flight-card")

        for card in cards:
            price_elem = card.query_selector(".fare-price")
            if price_elem:
                txt = price_elem.inner_text().replace("€", "").replace(",", ".").strip()
                try:
                    price = float(txt)
                    prices.append(price + 3.0)
                except:
                    pass

        browser.close()

    return prices
