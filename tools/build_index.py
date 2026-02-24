import os
import json
import hashlib
from pypdf import PdfReader
from bs4 import BeautifulSoup

TRANSPORT_DIR = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_FILE = os.path.join(TRANSPORT_DIR, "index.json")

USELESS_EXT = {".css", ".js", ".txt", ".md", ".docx", ".py", ".DS_Store", ".gitignore"}

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def extract_pdf_info(path):
    try:
        reader = PdfReader(path)
        first_page = reader.pages[0]
        text = first_page.extract_text() or ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        if not lines:
            return None  # PDF non indexable

        title = lines[0]
        if len(title) < 3:
            title = os.path.basename(path)

        description = " ".join(lines[1:4]) if len(lines) > 1 else ""

        date = ""
        for token in lines[:5]:
            if token[:4].isdigit():
                date = token[:10]
                break

        keywords = " ".join(lines[:10]).lower()

        return {
            "title": title,
            "path": os.path.basename(path),
            "description": description,
            "keywords": keywords,
            "date": date,
            "type": "pdf"
        }
    except:
        return None

def extract_html_info(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        title = soup.title.string.strip() if soup.title else os.path.basename(path)
        p = soup.find("p")
        description = p.get_text().strip() if p else ""

        return {
            "title": title,
            "path": os.path.basename(path),
            "description": description,
            "keywords": (title + " " + description).lower(),
            "date": "",
            "type": "html"
        }
    except:
        return None

def build_index():
    entries = []
    seen_hashes = {}
    duplicates = []
    non_indexable = []
    useless_files = []

    for filename in os.listdir(TRANSPORT_DIR):
        full_path = os.path.join(TRANSPORT_DIR, filename)

        if os.path.isdir(full_path):
            continue

        ext = os.path.splitext(filename)[1].lower()

        if ext in USELESS_EXT:
            useless_files.append(filename)
            continue

        if ext == ".pdf":
            h = file_hash(full_path)
            if h in seen_hashes:
                duplicates.append((filename, seen_hashes[h]))
                continue
            seen_hashes[h] = filename

            info = extract_pdf_info(full_path)
            if info is None:
                non_indexable.append(filename)
            else:
                entries.append(info)
            continue

        if ext == ".html":
            info = extract_html_info(full_path)
            if info is None:
                non_indexable.append(filename)
            else:
                entries.append(info)
            continue

        useless_files.append(filename)

    # TRI PAR DATE PUIS PAR NOM
    def sort_key(e):
        return (e["date"] if e["date"] else "0000-00-00", e["path"])

    entries.sort(key=sort_key, reverse=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\nIndex généré : {len(entries)} fichiers indexés.")
    print("Tri par date effectué.")

    if non_indexable:
        print("\nFichiers nécessitant une correction manuelle :")
        for f in non_indexable:
            print(f" - {f}")

    if useless_files:
        print("\nFichiers techniques ignorés (normaux) :")
        for f in useless_files:
            print(f" - {f}")

    if duplicates:
        print("\nDoublons détectés (déjà gérés précédemment) :")
        for a, b in duplicates:
            print(f" - {a} / {b}")

if __name__ == "__main__":
    build_index()
