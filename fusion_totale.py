import os, json, re
from pypdf import PdfReader

def extraire_date_precise(chemin_pdf):
    try:
        reader = PdfReader(chemin_pdf)
        nb_pages = len(reader.pages)
        # CAS ÉTUDE (> 20 pages) : On cherche en page 1
        if nb_pages > 20:
            texte = reader.pages[0].extract_text()
            match = re.search(r'\b(202[0-9]|201[0-9])\b', texte)
            if match: return match.group(1)
        # CAS ARTICLE : On cherche dans les 10 dernières lignes de la dernière page
        else:
            texte = reader.pages[-1].extract_text()
            if texte:
                lignes = texte.split('\n')
                for ligne in reversed(lignes[-10:]):
                    match = re.search(r'\b(202[0-9]|201[0-9])\b', ligne)
                    if match: return match.group(1)
    except:
        pass
    return None

# URLs SimDif vérifiées (plus de redirections vers l'accueil)
liens_web = [
    {"title": "Penser les transports (Portail)", "url": "https://pensertransports.simdif.com/index.html", "date": "2026-03-03"},
    {"title": "Mon Éditeur (L'Harmattan)", "url": "https://www.editions-harmattan.fr", "date": "2026"},
    {"title": "Le Rail", "url": "https://pensertransports.simdif.com/le-rail.html", "date": "2025"},
    {"title": "La Route", "url": "https://pensertransports.simdif.com/la-route.html", "date": "2025"},
    {"title": "Le Combiné", "url": "https://pensertransports.simdif.com/le-combine.html", "date": "2025"},
    {"title": "Les Statistiques", "url": "https://pensertransports.simdif.com/statistiques.html", "date": "2025"},
    {"title": "La Prospective", "url": "https://pensertransports.simdif.com/la-prospective.html", "date": "2026"}
]

files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
data_pdf = []

for f in files:
    date_doc = extraire_date_precise(f)
    if not date_doc:
        # Secours par le nom du fichier
        m = re.search(r'\b(19|20)\d{2}\b', f)
        date_doc = m.group(0) if m else "Archive"
    
    # Sécurité anti-404 : l'url DOIT être le nom exact du fichier
    data_pdf.append({
        "title": f.replace(".pdf", ""), 
        "url": f, 
        "date": date_doc
    })

# Tri : Les plus récents en haut
base_complete = liens_web + data_pdf
base_complete.sort(key=lambda x: str(x.get('date', '0000')), reverse=True)

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(base_complete, f, indent=2, ensure_ascii=False)

print(f"Restauration terminée : {len(data_pdf)} PDF liés sans erreur.")
