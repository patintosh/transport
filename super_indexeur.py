import os
import json
import PyPDF2

index_final = []
compteur = 0

# On liste tout dans le dossier actuel
fichiers = os.listdir('.')
print(f"DEBUG: Nombre total d'éléments vus par Python : {len(fichiers)}")

for nom in fichiers:
    # On gère .pdf ET .PDF
    if nom.lower().endswith('.pdf'):
        compteur += 1
        try:
            with open(nom, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # On prend les 600 premiers caractères pour la recherche
                texte = ""
                if len(reader.pages) > 0:
                    texte = reader.pages[0].extract_text()[:600]
                
                # Nettoyage du texte (enlève les retours à la ligne)
                texte = texte.replace('\n', ' ').strip()
                
                index_final.append({
                    "title": nom.replace('.pdf', '').replace('.PDF', ''),
                    "date": "Archive",
                    "category": "Transport",
                    "description": texte + "...",
                    "keywords": ["Fret", "Logistique", "Routier", "Maritime"],
                    "url": f"https://penser-transports.fr/pdf/{nom}"
                })
                print(f"✅ Indexé : {nom}")
        except Exception as e:
            print(f"❌ Erreur sur {nom} : {e}")

# Sauvegarde
with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(index_final, f, indent=2, ensure_ascii=False)

print(f"\n--- MISSION RÉUSSIE ---")
print(f"Total de PDF indexés : {len(index_final)}")
