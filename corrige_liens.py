
import json

filename = 'index.json'

with open(filename, 'r', encoding='utf-8') as f:
    data = json.load(f)

compteur = 0
for item in data:
    if "patricesalini.simdif.com" in item['path']:
        # On remplace l'ancienne adresse par la bonne
        item['path'] = item['path'].replace("patricesalini.simdif.com", "pensertransports.simdif.com")
        compteur += 1

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Correction terminée ! {compteur} lien(s) mis à jour vers https://pensertransports.simdif.com")