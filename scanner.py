import os, json, re

# Charger l'existant pour garder tes descriptions (rail, route, etc.)
existing_data = {}
if os.path.exists('index.json'):
    try:
        with open('index.json', 'r', encoding='utf-8') as j:
            for item in json.load(j):
                existing_data[item['url']] = item
    except: pass

def get_date(f):
    # Chercher année 19xx ou 20xx
    match = re.search(r'\b(19|20)\d{2}\b', f)
    return match.group(0) if match else "0000"

files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
final_data = []

for f in files:
    if f in existing_data:
        # ON GARDE TOUT : description, mots-clés, etc.
        item = existing_data[f]
        # On met juste à jour la date si elle est vide
        if not item.get('date') or item['date'] == "Archive":
            item['date'] = get_date(f)
        final_data.append(item)
    else:
        # Nouveau fichier
        final_data.append({
            "title": f.replace(".pdf", ""),
            "url": f,
            "date": get_date(f),
            "description": f.replace(".pdf", "")
        })

# Tri par date
final_data.sort(key=lambda x: x.get('date', '0000'), reverse=True)

with open('index.json', 'w', encoding='utf-8') as j:
    json.dump(final_data, j, indent=2, ensure_ascii=False)
