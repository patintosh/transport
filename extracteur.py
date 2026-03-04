import os
import json
import PyPDF2

# On charge l'index actuel (les 327 stables)
with open('index.json', 'r', encoding='utf-8') as f:
    catalogue = json.load(f)

# Liste des nouveaux fichiers à traiter (TM01 à TM78)
nouveaux_pdf = [f"TM{str(i).zfill(2)}.pdf" for i in range(1, 79)]
dossier_pdf = "pdf" # Assurez-vous que vos PDF sont dans ce dossier

for nom_fichier in nouveaux_pdf:
    chemin = os.path.join(dossier_pdf, nom_fichier)
    if os.path.exists(chemin):
        try:
            with open(chemin, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # On extrait le texte de la première page
                texte = reader.pages[0].extract_text()[:400].replace('\n', ' ')
                
                # Création du bloc JSON
                nouveau_bloc = {
                    "title": f"Archive {nom_fichier.replace('.pdf', '')}",
                    "date": "1990-1996",
                    "category": "Archives Historiques",
                    "description": texte + "...",
                    "keywords": ["Transport Routier", "Fret", "Logistique", "Archives"],
                    "url": f"https://penser-transports.fr/pdf/{nom_fichier}"
                }
                catalogue.append(nouveau_bloc)
                print(f"Indexé : {nom_fichier}")
        except Exception as e:
            print(f"Erreur sur {nom_fichier}: {e}")

# Sauvegarde finale propre
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(catalogue, f, indent=2, ensure_ascii=False)

print("--- EXTRACTION ET FUSION RÉUSSIES ---")
