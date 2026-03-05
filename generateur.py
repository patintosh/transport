import csv, json, re, os

csv_file = 'INVENTAIRE_CLEAN.csv'
glossary_file = 'glossaireinverse.json'
output_file = 'index.html'

# Configuration des onglets SimDif
ONGLETS_SIMDIF = [
    {"nom": "Politique des transports", "url": "https://pensertransports.simdif.com/où_est_passée_la_politique_des_transports.html", "contenu": "stratégie, planification, investissement"},
    {"nom": "Lyon-Turin", "url": "https://pensertransports.simdif.com/le_projet_lyon_turin_chapitrre_2.html", "contenu": "tunnel, fret, alpes"},
    {"nom": "Liaison Seine-Nord", "url": "https://pensertransports.simdif.com/la_liaison_seine_nord.html", "contenu": "canal, fluvial, logistique"}
]

data = []
glossary = {}

# Chargement du glossaire
if os.path.exists(glossary_file):
    with open(glossary_file, 'r', encoding='utf-8') as f:
        glossary = json.load(f)

# Lecture robuste du CSV
try:
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        # On force le point-virgule et on ignore les erreurs de lignes
        reader = csv.DictReader(f, delimiter=';')
        # Nettoyage automatique des noms de colonnes (enlever espaces et mettre en majuscules)
        reader.fieldnames = [n.strip().upper() for n in reader.fieldnames]
        
        for row in reader:
            t = (row.get('TITRE') or "").strip()
            if not t: continue # Saute les lignes vides
            
            u = (row.get('URL') or "").strip()
            d = (row.get('DATE') or "").strip()
            k = (row.get('KEYWORDS') or "").strip()
            
            # Extraction de l'année pour le tri
            year_match = re.search(r'(19|20)\d{2}', d + " " + t)
            year = int(year_match.group()) if year_match else 0
            
            data.append({'url': u, 'title': t, 'keywords': k, 'date': d, 'year': year})

    # Tri par défaut (Récent d'abord)
    data.sort(key=lambda x: x['year'], reverse=True)

    # Création du HTML (Structure fixe avec injection des données)
    html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bibliothèque P. Salini & C. Reynaud</title>
    <style>
        :root { --accent: #0056b3; }
        body { font-family: system-ui; background: #f1f5f9; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        header { background: white; padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }
        .wrapper { display: flex; flex-grow: 1; overflow: hidden; padding: 10px; gap: 10px; }
        .main { flex: 3; background: white; border-radius: 8px; display: flex; flex-direction: column; border: 1px solid #ccc; }
        .sidebar { flex: 1; background: white; border-radius: 8px; padding: 10px; border: 1px solid #ccc; overflow-y: auto; }
        .search-area { padding: 10px; border-bottom: 1px solid #eee; display: flex; gap: 5px; }
        #search { flex-grow: 1; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
        #global-list { overflow-y: auto; padding: 10px; }
        .card { background: #fff; border: 1px solid #eee; margin-bottom: 8px; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
        .title { font-weight: bold; color: #1e3a8a; font-size: 0.9em; }
        .date { font-size: 0.8em; color: #666; }
        .btn { text-decoration: none; padding: 5px 10px; background: var(--accent); color: white; border-radius: 4px; font-size: 0.8em; }
        @media (max-width: 768px) { .wrapper { flex-direction: column; } }
    </style>
</head>
<body>
    <header>
        <h1 style="margin:0; font-size:1.2em;">Bibliothèque P. Salini & C. Reynaud</h1>
        <div style="font-size:0.8em; margin-top:5px;">
            <a href="https://pensertransports.simdif.com">Site Principal</a> | 
            <a href="mailto:patrice.salini@wanadoo.fr">Contact</a>
        </div>
    </header>
    <div class="wrapper">
        <main class="main">
            <div class="search-area">
                <input type="search" id="search" placeholder="Rechercher parmi les documents...">
                <button onclick="toggleSort()" id="sortBtn" style="padding:10px; cursor:pointer;">▼ Récent</button>
            </div>
            <div id="counter" style="padding: 0 15px; font-size: 0.7em; font-weight: bold; color: #666;"></div>
            <div id="global-list"></div>
        </main>
        <aside class="sidebar">
            <h3 style="font-size:0.9em; margin-top:0;">Focus SimDif</h3>
            <div id="focus-list"></div>
        </aside>
    </div>
    <script>
        const docs = DOCS_JS;
        const glossary = GLOSSARY_JS;
        const onglets = ONGLETS_JS;
        let isDesc = true;

        function render() {
            const q = document.getElementById('search').value.toLowerCase().trim();
            let filtered = docs;
            if (q) {
                let terms = [q];
                if (glossary[q]) terms = [...terms, ...glossary[q].map(t => t.toLowerCase())];
                filtered = docs.filter(d => terms.some(t => (d.title + d.keywords).toLowerCase().includes(t)));
            }
            filtered.sort((a, b) => isDesc ? b.year - a.year : a.year - b.year);
            document.getElementById('counter').innerText = filtered.length + " documents affichés / " + docs.length + " au total";
            document.getElementById('global-list').innerHTML = filtered.map(d => `
                <div class="card">
                    <div>
                        <div class="title">${d.title}</div>
                        <div class="date">${d.date}</div>
                    </div>
                    <a href="${d.url}" target="_blank" class="btn">Lire</a>
                </div>
            `).join('');
        }
        function toggleSort() { isDesc = !isDesc; document.getElementById('sortBtn').innerText = isDesc ? "▼ Récent" : "▲ Ancien"; render(); }
        document.getElementById('search').addEventListener('input', render);
        window.onload = render;
    </script>
</body>
</html>"""

    final_html = html_template.replace('DOCS_JS', json.dumps(data, ensure_ascii=False))
    final_html = final_html.replace('GLOSSARY_JS', json.dumps(glossary, ensure_ascii=False))
    final_html = final_html.replace('ONGLETS_JS', json.dumps(ONGLETS_SIMDIF, ensure_ascii=False))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"✅ Succès ! {len(data)} documents intégrés dans index.html")

except Exception as e:
    print(f"❌ Erreur critique : {e}")
