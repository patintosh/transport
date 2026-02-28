import json

# LISTE DE VOS PAGES SIMDIF (À compléter selon vos besoins)
pages_simdif = [
    {
        "url": "https://patricesalini.simdif.com/index.html",
        "titre": "Accueil - Analyses Transports",
        "extrait": "Retrouvez l'ensemble des analyses sur le transport et la logistique par Patrice Salini."
    },
    {
        "url": "https://patricesalini.simdif.com/fret-ferroviaire.html",
        "titre": "Le déclin du fret ferroviaire",
        "extrait": "Analyse détaillée des causes du recul du fret ferroviaire en France depuis 30 ans."
    }
]

# Chargement de votre index actuel
with open('index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Ajout des pages
for page in pages_simdif:
    # On vérifie si elle n'existe pas déjà pour éviter les doublons
    if not any(item['path'] == page['url'] for item in data):
        data.append({
            "path": page["url"],
            "title": page["titre"],
            "description": page["extrait"],
            "date": "En ligne",
            "type_doc": "Site SimDif",
            "numero": "",
            "keywords": ["simdif", "web"]
        })

# Sauvegarde
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ {len(pages_simdif)} pages SimDif ajoutées à l'index !")