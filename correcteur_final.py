import json

# 1. Charger l'index actuel (les 367)
with open('index.json', 'r', encoding='utf-8') as f:
    catalogue = json.load(f)

# 2. Correction des URLs et Nettoyage
for article in catalogue:
    # On récupère le nom du fichier réel (ex: TM01.pdf)
    nom_fichier = article['url'].split('/')[-1]
    
    # On change l'URL pour qu'elle soit relative au site GitHub
    # Cela permet de cliquer et d'ouvrir le PDF qui est dans votre dossier /pdf/
    article['url'] = f"pdf/{nom_fichier}"
    
    # On s'assure que le titre est propre
    article['title'] = article['title'].replace('.pdf', '').replace('.PDF', '')

# 3. Tri par titre (Pour que TM01 vienne avant TM02, etc.)
# Si vous préférez trier par date, on peut, mais le titre est plus fiable ici
catalogue.sort(key=lambda x: x['title'])

# 4. Sauvegarde
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)

print("--- CORRECTION DES LIENS ET DU TRI TERMINÉE ---")
