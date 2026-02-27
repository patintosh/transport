import csv, json

# Charger l'index propre
with open("index.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Charger ton CSV
with open("anciens.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        fichier = row[0].strip()
        date = row[1].strip()

        numero = fichier.replace(".pdf", "")

        entry = {
            "path": fichier,
            "title": numero,
            "description": "",
            "date": date,
            "numero": numero
        }

        data.append(entry)

# Sauvegarder
with open("index.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
