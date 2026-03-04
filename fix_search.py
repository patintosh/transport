import os

if os.path.exists('search.js'):
    with open('search.js', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # On force l'attribut target="_blank" lors de la création des liens
    # On remplace les patterns classiques de création de liens en JS
    nouveau_code = code.replace(".href =", ".target = '_blank'; .href =")
    
    # Si le code utilise des template literals (avec ` `)
    if 'target="_blank"' not in nouveau_code:
        nouveau_code = nouveau_code.replace('<a href=', '<a target="_blank" href=')

    with open('search.js', 'w', encoding='utf-8') as f:
        f.write(nouveau_code)
    print("✅ search.js : Modifié pour ouvrir les PDF dans un nouvel onglet.")
else:
    print("❌ search.js introuvable.")
