import json, os

filename = 'index.json'

with open(filename, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    # On remplace les underscores par des tirets dans le chemin pour coller à vos fichiers
    if 'path' in item:
        item['path'] = item['path'].replace('_', '-')

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ index.json est maintenant synchronisé avec les tirets !")