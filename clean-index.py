{\rtf1\ansi\ansicpg1252\cocoartf2869
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import json\
import os\
\
INDEX_PATH = "index.json"        # ton index actuel\
DOCS_DIR = "docs"                # r\'e9pertoire des fichiers\
ROOT_DIR = "."                   # racine du d\'e9p\'f4t\
\
def file_exists(path):\
    """\
    V\'e9rifie si un fichier existe r\'e9ellement dans le d\'e9p\'f4t.\
    G\'e8re les chemins relatifs, les espaces, les encodages.\
    """\
    # chemins possibles\
    candidates = [\
        os.path.join(ROOT_DIR, path),\
        os.path.join(DOCS_DIR, path),\
        os.path.join(ROOT_DIR, os.path.basename(path)),\
        os.path.join(DOCS_DIR, os.path.basename(path)),\
    ]\
\
    for c in candidates:\
        if os.path.isfile(c):\
            return True\
    return False\
\
def main():\
    with open(INDEX_PATH, "r", encoding="utf-8") as f:\
        data = json.load(f)\
\
    cleaned = []\
    removed = []\
\
    for entry in data:\
        path = entry.get("path", "")\
        if file_exists(path):\
            cleaned.append(entry)\
        else:\
            removed.append(path)\
\
    # sauvegarde\
    with open(INDEX_PATH, "w", encoding="utf-8") as f:\
        json.dump(cleaned, f, ensure_ascii=False, indent=2)\
\
    print(f"Entr\'e9es conserv\'e9es : \{len(cleaned)\}")\
    print(f"Entr\'e9es supprim\'e9es : \{len(removed)\}")\
    print("\\nFichiers manquants :")\
    for r in removed:\
        print(" -", r)\
\
if __name__ == "__main__":\
    main()\
}