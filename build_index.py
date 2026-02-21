import os
import json
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from PyPDF2 import PdfReader

ROOT = "."
HTML_DIR = "."
PDF_DIR = "."

OUTPUT = "index.json"

def file_id(path):
    """ID stable basé sur un hash court."""
    h = hashlib.sha1(path.encode("utf-8")).hexdigest()
    return h[:6].upper()

def extract_html_info(filepath):
    """Extrait titre, snippet et texte d'un fichier HTML."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Titre
    title = soup.title.string.strip() if soup.title else os.path.basename(filepath)

    # Snippet : première phrase propre
    text = soup.get_text(" ", strip=True)
    snippet = text[:200] + "..." if len(text) > 200 else text

    return title, snippet

def extract_pdf_info(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages[:3]:
            text += page.extract_text() or ""
        text = text.strip()
        if not text:
            return ("PDF sans texte", "")
        return (os.path.basename(filepath), text[:300])
    except Exception:
        return ("PDF illisible", "")

def build_entry(path, fullpath, ftype):
    """Construit une entrée JSON complète."""
    stat = os.stat(fullpath)
    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

    if ftype == "html":
        title, snippet = extract_html_info(fullpath)
    else:
        title, snippet = extract_pdf_info(fullpath)

    return {
        "id": file_id(path),
        "path": path,
        "title": title,
        "snippet": snippet,
        "type": ftype,
        "size": stat.st_size,
        "modified": modified
    }

def main():
    entries = []

    # HTML
    for fname in os.listdir(HTML_DIR):
        if fname.lower().endswith(".html"):
            path = fname
            fullpath = os.path.abspath(path)
            entries.append(build_entry(path, fullpath, "html"))

    # PDF
    for fname in os.listdir(PDF_DIR):
        if fname.lower().endswith(".pdf"):
            path = fname
            fullpath = os.path.abspath(path)
            entries.append(build_entry(path, fullpath, "pdf"))

    # Sauvegarde
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Index généré : {OUTPUT} ({len(entries)} entrées)")

if __name__ == "__main__":
    main()
