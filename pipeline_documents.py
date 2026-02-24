import os
import json
import re
import shutil
from pdfminer.high_level import extract_text as pdf_extract
from pdfminer.pdfpage import PDFPage
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

DOCS_DIR = "."
INDEX_FILE = "index.json"
TO_REPLACE_FILE = "to_replace.json"
GLOSSAIRE_INVERSE_FILE = "glossaire_inverse.json"

# ------------------------------------------------------------
# Chargement du glossaire inverse
# ------------------------------------------------------------
def load_glossaire_inverse():
    if os.path.exists(GLOSSAIRE_INVERSE_FILE):
        with open(GLOSSAIRE_INVERSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ------------------------------------------------------------
# Extraction du texte PDF
# ------------------------------------------------------------
def extract_text(path):
    try:
        return pdf_extract(path)
    except:
        return ""

# ------------------------------------------------------------
# Nettoyage du texte PDF
# ------------------------------------------------------------
def clean_text(text):
    # Supprimer les lignes trop courtes (numéros de page, pieds de page)
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if len(l) > 5]

    # Supprimer les répétitions exactes (pieds de page répétés)
    seen = set()
    cleaned = []
    for l in lines:
        if l not in seen:
            cleaned.append(l)
            seen.add(l)

    # Rejoindre proprement
    text = " ".join(cleaned)

    # Normalisation espaces
    text = re.sub(r"\s+", " ", text)

    # Nettoyage guillemets JSON
    text = text.replace('"', "'")

    return text.strip()

# ------------------------------------------------------------
# Description courte (propre, éditoriale)
# ------------------------------------------------------------
def extract_description(text):
    # On prend les 2–3 premières phrases
    sentences = re.split(r"(?<=[.!?])\s+", text)
    short = " ".join(sentences[:3])

    # Tronquer proprement
    if len(short) > 300:
        short = short[:300].rsplit(" ", 1)[0] + " (…)"

    return short

def extract_internal_title(text):
    # On découpe en lignes
    lines = [l.strip() for l in text.splitlines()]

    # Expressions à ignorer
    ignore_patterns = [
        r"^page\s*\d+",          # Page 1, Page 12…
        r"^\d+$",                # lignes purement numériques
        r"^\d{1,2}[./]\d{1,2}[./]\d{2,4}$",  # dates
        r"^(19|20)\d{2}$",       # année seule
        r"^sommaire$", r"^résumé$", r"^resume$",
        r"^introduction$", r"^conclusion$",
        r"^table\s+des\s+matières$",
    ]

    for line in lines:
        if not line:
            continue

        # Trop court pour être un titre
        if len(line) < 8:
            continue

        # Trop long = probablement un paragraphe
        if len(line) > 200:
            continue

        # Ignorer les lignes en MAJUSCULES complètes (souvent en-têtes)
        if line.isupper():
            continue

        # Ignorer les motifs indésirables
        if any(re.match(p, line, flags=re.IGNORECASE) for p in ignore_patterns):
            continue

        # Si on arrive ici, c'est probablement un vrai titre
        return line

    # Fallback : nom du fichier sans extension
    return ""


# ------------------------------------------------------------
# Extraction intelligente de la date modif 24 fev 10:54
# ------------------------------------------------------------
def extract_date(text):
    first_part = text[:800]

    mois = {
        "janvier": "01", "février": "02", "fevrier": "02",
        "mars": "03", "avril": "04", "mai": "05",
        "juin": "06", "juillet": "07",
        "août": "08", "aout": "08",
        "septembre": "09", "octobre": "10",
        "novembre": "11", "décembre": "12", "decembre": "12"
    }

    # JJ mois AAAA
    m = re.search(r"(\d{1,2})\s+(" + "|".join(mois.keys()) + r")\s+(\d{4})",
                  first_part, flags=re.IGNORECASE)
    if m:
        day = m.group(1).zfill(2)
        month_name = m.group(2).lower()
        year = int(m.group(3))
        if 1950 <= year <= 2025:
            return f"{day}.{mois[month_name]}.{year}"

    # JJ.MM.AAAA
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", first_part)
    if m:
        d = m.group(1).zfill(2)
        mth = m.group(2).zfill(2)
        year = int(m.group(3))
        if 1950 <= year <= 2025:
            return f"{d}.{mth}.{year}"

    # Année seule
    m = re.search(r"(19|20)\d{2}", first_part)
    if m:
        year = int(m.group(0))
        if 1950 <= year <= 2025:
            return str(year)

    return ""


# ------------------------------------------------------------
# Nombre de pages
# ------------------------------------------------------------
def extract_page_count(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in PDFPage.get_pages(f))
    except:
        return 0

# ------------------------------------------------------------
# Type de document
# ------------------------------------------------------------
def classify_document(page_count):
    return "Article" if page_count < 15 else "Étude"

# ------------------------------------------------------------
# Enrichissement des mots-clés
# ------------------------------------------------------------
def enrich_keywords(text, glossaire_inverse):
    words = set(text.lower().split())
    keywords = set()

    for w in words:
        if w in glossaire_inverse:
            for principal in glossaire_inverse[w]:
                keywords.add(principal)

    return list(keywords)

# ------------------------------------------------------------
# Pipeline principal
# ------------------------------------------------------------
def main():
    clean_index = []
    to_replace = []

    glossaire_inverse = load_glossaire_inverse()

    for filename in os.listdir(DOCS_DIR):
        path = os.path.join(DOCS_DIR, filename)

        if not os.path.isfile(path):
            continue

        if filename in ["index.json", "to_replace.json", "pipeline_documents.py",
                        "search.js", "styles.css", "index.html",
                        "glossaire.json", "glossaire_inverse.json"]:
            continue

        if filename.lower().endswith(".pdf"):
            raw = extract_text(path)
            text = clean_text(raw)

            pages = extract_page_count(path)
            type_doc = classify_document(pages)
            keywords = enrich_keywords(text, glossaire_inverse)

            clean_index.append({
                "title": os.path.splitext(filename)[0],
                "path": filename,
                "description": extract_description(text),
                "date": extract_date(text),
                "numero": extract_internal_title(text),
                "type_doc": type_doc,
                "keywords": keywords
            })
            continue

        if filename.lower().endswith(".html"):
            to_replace.append({
                "path": filename,
                "reason": "HTML exclu"
            })
            continue

    # Tri final par date (descendant)
    clean_index.sort(key=lambda d: d["date"], reverse=True)

    with open("index_clean.json", "w", encoding="utf-8") as f:
        json.dump(clean_index, f, indent=2, ensure_ascii=False)

    with open(TO_REPLACE_FILE, "w", encoding="utf-8") as f:
        json.dump(to_replace, f, indent=2, ensure_ascii=False)

    shutil.move("index_clean.json", INDEX_FILE)

    print("\n🎯 Pipeline terminé.")
    print(f"PDF indexés : {len(clean_index)}")
    print(f"HTML exclus : {len(to_replace)}")

if __name__ == "__main__":
    main()
