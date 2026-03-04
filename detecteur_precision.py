import json
import os
import re
from pypdf import PdfReader

def trouver_vraie_date(nom_fichier, texte_debut, texte_fin):
    # 1. Chercher une année à 4 chiffres (1990-2026) dans le NOM du fichier
    # Exemple: "1994 Édito TM N° 6.pdf" -> 1994
    match_nom = re.search(r'\b(19|20)\d{2}\b', nom_fichier)
    if match_nom:
        return match_nom.group(0)

    # 2. Chercher "P.S. JJ/MM/AAAA" à la FIN du document
    if texte_fin:
        match_ps = re.search(r'P\.S\.\s*(\d{2}/\d{2}/\d{4})', texte_fin)
        if match_ps:
            return match_ps.group(1)

    # 3. Chercher une date complète JJ/MM/AAAA au DEBUT ou à la FIN
    for zone in [texte_debut, texte_fin]:
        if zone:
            match_date = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', zone)
            if match_date:
                return match_date.group(0)

    # 4. Chercher une année seule à 4 chiffres dans le texte
    for zone in [texte_fin, texte_debut]:
        if zone:
            match_annee = re.search(r'\b(19|20)\d{2}\b', zone)
            if match_annee:
                return match_annee.group(0)
    
    return "Archive"

with open('index.json', 'r', encoding='utf-8') as f:
    catalogue = json.load(f)

print("🔍 Analyse de précision (Année > P.S. > Texte)...")

for article in catalogue:
    pdf_path = os.path.join('pdf', article['title'] + ".pdf")
    if not os.path.exists(pdf_path): continue

    try:
        reader = PdfReader(pdf_path)
        debut = reader.pages[0].extract_text()[:1000]
        fin = reader.pages[-1].extract_text()[-1000:]
        
        nouvelle_date = trouver_vraie_date(article['title'], debut, fin)
        
        if nouvelle_date != article['date']:
            print(f"✅ {article['title']} : {article['date']} -> {nouvelle_date}")
            article['date'] = nouvelle_date
    except:
        continue

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)

print("\n🚀 Correction terminée !")
