import json, os, re, unicodedata

def slugify(text):
    if not text: return ""
    name, ext = os.path.splitext(text)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    # LA LIGNE MAGIQUE : on force tout en minuscules pour le lien
    return (name + ext).lower() 

with open('index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    item['path'] = slugify(item.get('path', ''))
    item['numero'] = ""

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("✅ Terminé : Tout le JSON est en minuscules !")