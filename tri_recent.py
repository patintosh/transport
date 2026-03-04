import json

BASE_URL = "https://patintosh.github.io/transport/pdf/"

with open('index.json', 'r', encoding='utf-8') as f:
    catalogue = json.load(f)

for article in catalogue:
    # On s'assure que l'URL est bien complète pour GitHub Pages
    nom_fichier = article['url'].split('/')[-1]
    article['url'] = BASE_URL + nom_fichier

# TRI : On met les plus récents (TM78, TM77...) en haut
# reverse=True permet de trier de Z à A (ou du plus grand au plus petit)
catalogue.sort(key=lambda x: x['title'], reverse=True)

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)

print("--- TRI RÉCENT EN TÊTE ET URLS FIXÉES ---")
