import json
import os

INDEX_PATH = "index.json"        # ton index actuel
DOCS_DIR = "docs"                # répertoire des fichiers
ROOT_DIR = "."                   # racine du dépôt

def file_exists(path):
    """
    Vérifie si un fichier existe réellement dans le dépôt.
    Gère les chemins relatifs, les espaces, les encodages.
    """
    candidates = [
        os.path.join(ROOT_DIR, path),
        os.path.join(DOCS_DIR, path),
        os.path.join(ROOT_DIR, os.path.basename(path)),
        os.path.join(DOCS_DIR, os.path.basename(path)),
    ]

    for c in candidates:
        if os.path.isfile(c):
            return True
    return False

def main():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = []
    removed = []

    for entry in data:
        path = entry.get("path", "")
        if file_exists(path):
            cleaned.append(entry)
        else:
            removed.append(path)

    # sauvegarde
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"Entrées conservées : {len(cleaned)}")
    print(f"Entrées supprimées : {len(removed)}")
    print("\nFichiers manquants :")
    for r in removed:
        print(" -", r)

if __name__ == "__main__":
    main()
