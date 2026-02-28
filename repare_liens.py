import json
import os

# 1. Lister tous les PDF réellement présents dans le dossier
fichiers_reels = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]

# 2. Charger le JSON
with open('index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Synchronisation en cours...")

for item in data:
    path_json = item.get('path', '').lower()
    
    # On cherche si un fichier réel correspond (sans tenir compte des tirets/underscores)
    nom_simplifie_json = path_json.replace('_', '-').replace(' ', '-')
    
    for reel in fichiers_reels:
        nom_simplifie_reel = reel.lower().replace('_', '-').replace(' ', '-')
        
        if nom_simplifie_json == nom_simplifie_reel:
            if item['path'] != reel:
                print(f"Correction : {item['path']} -> {reel}")
                item['path'] = reel # On met le nom exact du fichier disque

# 3. Sauvegarder
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Terminé ! Le JSON est maintenant le miroir exact de votre dossier.")