
import requests
from bs4 import BeautifulSoup
import json
import os
import urllib.parse

SITE_URL = "https://pensertransports.simdif.com"

PAGES = [
    "index.html", "qui_sommes_nous.html", "où_est_passée_la_politique_des_transports.html",
    "le_grand_projet_lyon-turin.html", "le_projet_lyon_turin_chapitrre_2.html",
    "la_liaison_seine_nord.html", "les_prévisions_de_transport.html",
    "l’évaluation_des_politiques_et_des_projets_publics.html", "les_questions_sociales.html",
    "l’europe_des_transports.html", "le_fret_ferroviaire.html", "le_transport_routier.html",
    "les_politiques_de_voisinage.html", "territoires,_transports,_et_démocratie.html",
    "mesurer_les_transports_de_fret.html", "la_tarification_des_infrastructures.html",
    "débat_général_sur_les_politiques_publiques.html", "la_lente_incompréhension_des_enjeux.html",
    "les_empires_et_les_réseaux.html", "mobilité_militaire_et_union_européenne_dialogue_de_sourds_.html",
    "a_l_origine_des_corridors.html"
]

def scraper_simdif():
    if not os.path.exists("index.json"):
        print("Erreur : index.json absent")
        return
        
    with open("index.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"🧹 Nettoyage des accents et du menu pour {len(PAGES)} pages...")

    for page in PAGES:
        encoded_page = urllib.parse.quote(page)
        full_url = f"{SITE_URL}/{encoded_page}"
        
        try:
            # On force le décodage en UTF-8 pour éviter les Ã©
            response = requests.get(full_url, timeout=10)
            response.encoding = 'utf-8' 
            
            if response.status_code != 200: continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # --- ON SUPPRIME LE MENU ET LE FOOTER AVANT DE LIRE ---
            for junk in soup.find_all(['nav', 'footer', 'header', 'form']):
                junk.decompose()

            # Titre propre
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text().strip() if title_tag else page
            
            # On ne prend que les paragraphes de l'article (au moins 50 caractères)
            # Cela évite d'attraper les mots isolés comme "Menu" ou "Contact"
            paragraphs = []
            for p in soup.find_all('p'):
                txt = p.get_text().strip()
                if len(txt) > 50 and "contact" not in txt.lower():
                    paragraphs.append(txt)
            
            # On ne garde que les 3 premiers paragraphes (environ 300-400 car.)
            clean_text = " ".join(paragraphs[:3])
            
            # On met à jour l'entrée
            new_entry = {
                "path": f"{SITE_URL}/{page}",
                "title": title,
                "description": clean_text[:400] + "...",
                "date": "2026",
                "type_doc": "Site Web"
            }

            # Remplacement sans doublon
            data = [item for item in data if item['path'] != new_entry['path']]
            data.append(new_entry)
            print(f"✅ Nettoyé : {title[:40]}...")

        except Exception as e:
            print(f"❌ Erreur sur {page}: {e}")

    # SAUVEGARDE CRUCIALE AVEC UTF-8 FORCÉ
    with open("index.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scraper_simdif()