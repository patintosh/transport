import os, json, re

# 1. Charger les données actuelles (même si elles sont abîmées, on va les réparer)
old_data = []
if os.path.exists('index.json'):
    with open('index.json', 'r', encoding='utf-8') as f:
        old_data = json.load(f)

# On crée un dictionnaire pour indexer par URL (minuscule pour la comparaison)
lookup = {item['url'].lower(): item for item in old_data}

# 2. Scanner le dossier pour trouver TOUS les PDF présents (Anciens + 72 Nouveaux)
files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
final_list = []

print(f"--- Scan du dossier : {len(files)} fichiers PDF trouvés ---")

for f in files:
    key = f.lower()
    if key in lookup:
        # On garde l'existant (Glossaire, Rail, etc.)
        item = lookup[key]
        item['url'] = f # ON RÉPARE LA CASSE (A0231.pdf)
        final_list.append(item)
    else:
        # C'est un des nouveaux fichiers
        year_match = re.search(r'\b(19|20)\d{2}\b', f)
        final_list.append({
            "title": f.replace(".pdf", ""),
            "url": f,
            "date": year_match.group(0) if year_match else "2026",
            "description": f.replace(".pdf", "").replace("-", " ")
        })

# 3. Récupérer les liens WEB (SimDif) qui n'ont pas de PDF local
for item in old_data:
    if not item['url'].lower().endswith('.pdf'):
        final_list.append(item)

# Tri par date décroissante
def sort_key(x):
    d = str(x.get('date', '0000'))
    if "2026" in d: return "9999" + d
    return d

final_list.sort(key=sort_key, reverse=True)

with open('index.json', 'w', encoding='utf-8') as j:
    json.dump(final_list, j, indent=2, ensure_ascii=False)

print(f"--- Résultat : {len(final_list)} entrées au total dans index.json ---")
