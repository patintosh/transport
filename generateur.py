import csv, json, re, os

csv_file = 'INVENTAIRE_CLEAN.csv'
glossary_file = 'glossaireinverse.json'
output_file = 'index.html'

# RESTAURATION DES LIENS SITES INTERNET
ONGLETS_SIMDIF = [
    {"nom": "Politique des transports", "url": "https://pensertransports.simdif.com/où_est_passée_la_politique_des_transports.html", "contenu": "stratégie nationale, planification, investissement"},
    {"nom": "Lyon-Turin (Chap. 2)", "url": "https://pensertransports.simdif.com/le_projet_lyon_turin_chapitrre_2.html", "contenu": "tunneliers, géologie, fret"},
    {"nom": "Liaison Seine-Nord", "url": "https://pensertransports.simdif.com/la_liaison_seine_nord.html", "contenu": "canal, fluvial, grand gabarit"},
    {"nom": "Prévisions de transport", "url": "https://pensertransports.simdif.com/les_prévisions_de_transport.html", "contenu": "modélisation, trafic futur, statistiques"},
    {"nom": "Évaluation des politiques", "url": "https://pensertransports.simdif.com/l’évaluation_des_politiques_et_des_projets_publics.html", "contenu": "socio-économie, rentabilité"},
    {"nom": "Questions sociales", "url": "https://pensertransports.simdif.com/les_questions_sociales.html", "contenu": "emploi, syndicats, grèves"},
    {"nom": "Europe des transports", "url": "https://pensertransports.simdif.com/l’europe_des_transports.html", "contenu": "paquet ferroviaire, bruxelles"},
    {"nom": "Fret ferroviaire", "url": "https://pensertransports.simdif.com/le_fret_ferroviaire.html", "contenu": "sncf, trains, wagon isolé"},
    {"nom": "Transport routier", "url": "https://pensertransports.simdif.com/le_transport_routier.html", "contenu": "camions, pavillon, autoroutes"},
    {"nom": "Exemple Suisse", "url": "https://pensertransports.simdif.com/l’exemple_suisse.html", "contenu": "transit, alpes, redevance"},
    {"nom": "Territoires & Démocratie", "url": "https://pensertransports.simdif.com/territoires,_transports,_et_démocratie.html", "contenu": "gilets jaunes, décentralisation"}
]

data = []
glossary = {}

if os.path.exists(glossary_file):
    with open(glossary_file, 'r', encoding='utf-8') as f:
        glossary = json.load(f)

try:
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        reader.fieldnames = [n.strip().upper() for n in reader.fieldnames]
        for row in reader:
            t = (row.get('TITRE') or "").strip()
            if not t: continue
            u = (row.get('URL') or "").strip()
            d = (row.get('DATE') or "").strip()
            k = (row.get('KEYWORDS') or "").strip()
            year_match = re.search(r'(19|20)\d{2}', d + " " + t)
            year = int(year_match.group()) if year_match else 0
            data.append({'url': u, 'title': t, 'keywords': k, 'date': d, 'year': year})

    data.sort(key=lambda x: x['year'], reverse=True)

    html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bibliothèque P. Salini & C. Reynaud</title>
    <style>
        :root { --accent: #0056b3; --video: #059669; --bg: #f8fafc; }
        body { margin: 0; font-family: 'Segoe UI', system-ui, sans-serif; background: #f1f5f9; height: 100vh; display: flex; flex-direction: column; color: #1e293b; }
        
        header { background: white; padding: 15px 20px; text-align: center; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
        h1 { margin: 0 0 10px 0; font-size: 1.5em; color: #1e3a8a; }
        
        .nav-sites { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-bottom: 5px; }
        .nav-sites a { text-decoration: none; color: var(--accent); font-weight: 600; font-size: 0.75em; padding: 6px 12px; background: #f1f5f9; border-radius: 20px; border: 1px solid #e2e8f0; transition: all 0.2s; }
        .nav-sites a:hover { background: var(--accent); color: white; }

        .wrapper { display: flex; flex-grow: 1; overflow: hidden; padding: 12px; gap: 12px; }
        .sidebar { width: 300px; background: white; border-radius: 12px; display: flex; flex-direction: column; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .main { flex-grow: 1; background: white; border-radius: 12px; display: flex; flex-direction: column; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

        .search-area { padding: 15px; border-bottom: 1px solid #f1f5f9; display: flex; gap: 10px; align-items: center; background: #fcfcfd; }
        #search { flex-grow: 1; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e0; font-size: 16px; outline: none; }
        #search:focus { border-color: var(--accent); ring: 2px solid #bfdbfe; }
        .btn-sort { padding: 10px 15px; background: white; border: 1px solid #cbd5e0; border-radius: 8px; cursor: pointer; font-size: 0.85em; font-weight: 600; white-space: nowrap; }

        #global-list { overflow-y: auto; padding: 15px; }
        .card { background: white; margin-bottom: 10px; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; gap: 15px; transition: transform 0.1s; }
        .card:hover { border-color: #cbd5e0; background: #fafafa; }
        .title { font-weight: 700; color: #1e3a8a; font-size: 0.95em; line-height: 1.4; flex-grow: 1; }
        .date-tag { font-size: 0.75em; color: #64748b; background: #f1f5f9; padding: 3px 8px; border-radius: 6px; margin-top: 5px; display: inline-block; }
        
        .actions { display: flex; gap: 8px; }
        .btn-action { text-decoration: none; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; color: white; font-weight: bold; transition: opacity 0.2s; }
        .btn-view { background: var(--accent); }
        .btn-dl { background: #64748b; }

        @media (max-width: 768px) {
            .wrapper { flex-direction: column; overflow-y: auto; }
            .sidebar { width: 100%; order: 2; height: auto; }
            .main { width: 100%; order: 1; height: auto; min-height: 500px; }
            body { height: auto; display: block; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Bibliothèque Patrice Salini & Christian Reynaud</h1>
        <div class="nav-sites">
            <a href="https://pensertransports.simdif.com" target="_blank">Penser les Transports</a>
            <a href="https://www.editions-harmattan.fr/catalogue/auteur/patrice-salini/15031" target="_blank">L'Harmattan</a>
            <a href="https://www.transportinfo.fr/?s=patrice+Salini" target="_blank">Transport Info</a>
            <a href="mailto:patrice.salini@wanadoo.fr">✉ Contact</a>
        </div>
    </header>

    <div class="wrapper">
        <main class="main">
            <div class="search-area">
                <input type="search" id="search" placeholder="Rechercher un titre ou mot-clé...">
                <button id="sortBtn" class="btn-sort" onclick="toggleSort()">▼ Récent</button>
            </div>
            <div id="counter" style="padding: 8px 15px; font-size: 0.75em; color: #64748b; font-weight: bold; background: #f8fafc; border-bottom: 1px solid #f1f5f9;"></div>
            <div id="global-list"></div>
        </main>
        <aside class="sidebar">
            <div style="padding:15px; font-weight:bold; color: #1e3a8a; border-bottom: 1px solid #f1f5f9; background: #fcfcfd; border-radius: 12px 12px 0 0;">Focus thématique (SimDif)</div>
            <div id="focus-list" style="padding: 10px;"></div>
        </aside>
    </div>

    <script>
        const docs = DOCS_JS;
        const glossary = GLOSSARY_JS;
        const onglets = ONGLETS_JS;
        let isDesc = true;

        function render() {
            const query = document.getElementById('search').value.toLowerCase().trim();
            let filtered = [...docs];
            
            if (query) {
                let terms = [query];
                if (glossary[query]) terms = [...terms, ...glossary[query].map(t => t.toLowerCase())];
                filtered = docs.filter(d => terms.some(t => (d.title + d.keywords).toLowerCase().includes(t)));
                
                const matchedOnglets = onglets.filter(o => terms.some(t => (o.nom + o.contenu).toLowerCase().includes(t)));
                document.getElementById('focus-list').innerHTML = matchedOnglets.map(o => `
                    <a href="${o.url}" target="_blank" style="display:block; text-decoration:none; background:#eff6ff; padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid var(--accent); color:#1e3a8a; font-size:0.8em; font-weight:bold;">${o.nom} →</a>
                `).join('') || '<p style="text-align:center;font-size:0.7em;color:#94a3b8;">Aucun lien SimDif</p>';
            } else {
                document.getElementById('focus-list').innerHTML = '<p style="text-align:center;color:#94a3b8;font-size:0.75em;padding:20px;">Le lien SimDif apparaîtra ici selon votre recherche.</p>';
            }

            filtered.sort((a, b) => isDesc ? b.year - a.year : a.year - b.year);
            document.getElementById('counter').innerText = filtered.length + " documents (Total : " + docs.length + ")";
            
            document.getElementById('global-list').innerHTML = filtered.map(d => `
                <div class="card">
                    <div style="flex-grow:1">
                        <div class="title">${d.title}</div>
                        <span class="date-tag">${d.date}</span>
                    </div>
                    <div class="actions">
                        <a href="${d.url}" target="_blank" class="btn-action btn-view" title="Ouvrir">👁</a>
                        <a href="${d.url}" download class="btn-action btn-dl" title="Télécharger">💾</a>
                    </div>
                </div>
            `).join('');
        }

        function toggleSort() {
            isDesc = !isDesc;
            document.getElementById('sortBtn').innerText = isDesc ? "▼ Récent" : "▲ Ancien";
            render();
        }
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
    print(f"✅ Terminé : {len(data)} docs, liens restaurés et style amélioré.")

except Exception as e:
    print(f"❌ Erreur : {e}")
