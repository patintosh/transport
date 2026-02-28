import json
import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        # On prend le début (page 1)
        first_page = reader.pages[0].extract_text()
        # On prend la fin (dernière page)
        last_page = reader.pages[-1].extract_text()
        
        # On nettoie un peu le texte (300 premiers caractères du début et de la fin)
        debut = " ".join(first_page.split()[:50]) # ~50 premiers mots
        fin = " ".join(last_page.split()[-30:])   # ~30 derniers mots
        
        return f"{debut} [...] {fin}"
    except Exception as e:
        return None

# Chargement du JSON
with open('index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Début de l'extraction, cela peut prendre quelques minutes...")

for item in data:
    path = item.get('path')
    if path and os.path.exists(path):
        # On ne le fait que si la description est générique
        if "Document :" in item['description'] or not item['description']:
            texte_reel = extract_text_from_pdf(path)
            if texte_reel:
                item['description'] = texte_reel
                print(f"✅ Texte extrait pour : {path}")

# Sauvegarde
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n🚀 Félicitations ! Votre index.json contient maintenant les vrais résumés des PDF.")