import os
import json

ROOT = "docs"

def guess_title(filename):
    name = os.path.splitext(filename)[0]
    name = name.replace("_", " ").replace("-", " ")
    return name.strip()

entries = []

for root, dirs, files in os.walk(ROOT):
    for f in files:
        if f.lower().endswith((".pdf", ".html", ".htm", ".docx", ".txt")):
            rel_path = os.path.join(root, f).replace("\\", "/")
            entries.append({
                "title": guess_title(f),
                "path": rel_path,
                "type": os.path.splitext(f)[1].lstrip(".").lower()
            })

# Tri alphabétique pour stabilité
entries.sort(key=lambda x: x["title"].lower())

with open("index.json", "w", encoding="utf-8") as out:
    json.dump(entries, out, indent=2, ensure_ascii=False)

print(f"{len(entries)} entrées écrites dans index.json")
