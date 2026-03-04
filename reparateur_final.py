import json
import os

# 1. RÉPARATION DE L'INDEX (Tri et URLs)
if os.path.exists('index.json'):
    with open('index.json', 'r', encoding='utf-8') as f:
        catalogue = json.load(f)
    
    BASE_URL = "https://patintosh.github.io/transport/pdf/"
    for article in catalogue:
        nom_fichier = article['url'].split('/')[-1]
        article['url'] = BASE_URL + nom_fichier
    
    # Tri : Plus récent (Z-A) en tête
    catalogue.sort(key=lambda x: x['title'], reverse=True)
    
    with open('index.json', 'w', encoding='utf-8') as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)
    print("✅ index.json : Trié (récent en tête) et URLs réparées.")

# 2. RÉPARATION DU COMPORTEMENT (script.js)
if os.path.exists('script.js'):
    with open('script.js', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # On force l'ouverture dans un nouvel onglet pour tous les liens <a>
    if 'target' not in code:
        # On cherche la création de lien dans votre JS et on injecte le target blank
        code = code.replace("a.href =", "a.target = '_blank'; a.href =")
        code = code.replace("link.href =", "link.target = '_blank'; link.href =")
        
        with open('script.js', 'w', encoding='utf-8') as f:
            f.write(code)
        print("✅ script.js : Liens forcés vers un nouvel onglet.")
