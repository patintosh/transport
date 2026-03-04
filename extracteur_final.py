import os
import json
import PyPDF2

# 1. Charger l'index actuel (les 320)
with open('index.json', 'r', encoding='utf-8') as f:
    catalogue = json.load(f)

titres_existants = {item['title'].lower() for item in catalogue}
dossier_pdf = "pdf"
ajouts = 0

# 2. Scanner TOUS les PDF du dossier pour trouver les manquants
if os.path.exists(dossier_pdf):
    for nom_fichier in os.listdir(dossier_pdf):
        if nom_fichier.endswith(".pdf"):
            titre_temp = f"Archive {nom_fichier.replace('.pdf', '')}"
            
            # Si cet article n'est pas encore dans l'index, on l'ajoute
            if titre_temp.lower() not in titres_existants:
                try:
                    with open(os.path.join(dossier_pdf, nom_fichier), 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        texte = reader.pages[0].extract_text()[:500].replace('\n', ' ')
                        
                        nouveau_bloc = {
                            "title": titre_temp,
                            "date": "1990-1996",
                            "category": "Archives Historiques",
                            "description": texte + "...",
                            "keywords": ["Transport", "Fret", "Logistique", "Archives"],
                            "url": f"https://penser-transports.fr/pdf/{nom_fichier}"
                        }
                        catalogue.append(nouveau_bloc)
                        titres_existants.add(titre_temp.lower())
                        ajouts += 1
                except:
                    pass

# 3. Sauvegarde propre
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)

print(f"--- FUSION TERMINÉE : {ajouts} articles ajoutés ---")
