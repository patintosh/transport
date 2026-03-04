import json, os

with open('index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for it in data:
    title = it.get('title', '').upper()
    desc = it.get('description', '')
    
    # Injection intelligente de mots-clés selon tes codes habituels
    mots_cles = []
    if "A02" in title or "A03" in title or "FER" in title:
        mots_cles.extend(["Rail", "Ferroviaire", "Train", "Fret"])
    if "A01" in title or "ROUTE" in title or "ROUT" in title:
        mots_cles.extend(["Route", "Routier", "Camion", "Marchandises"])
    if "A04" in title or "COMB" in title:
        mots_cles.extend(["Combiné", "Multimodal", "Logistique"])
    if "TARNOS" in title:
        mots_cles.extend(["Tarnos", "Logistique urbaine", "TIH"])

    # On enrichit la description sans écraser ce qui existe déjà
    nouveaux_mots = ", ".join(mots_cles)
    if nouveaux_mots and nouveaux_mots.lower() not in desc.lower():
        it['description'] = f"{desc} ({nouveaux_mots})".strip(" ()")

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Glossaire enrichi par logique de codes.")
