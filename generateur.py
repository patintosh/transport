import csv, json, re, os

csv_file = 'INVENTAIRE_CLEAN.csv'
glossary_file = 'glossaireinverse.json'
output_file = 'index.html'

ONGLETS_SIMDIF = [
    {"nom": "Politique des transports", "url": "https://pensertransports.simdif.com/où_est_passée_la_politique_des_transports.html", "contenu": "stratégie nationale, planification, investissement, infrastructures, grands projets"},
    {"nom": "Lyon-Turin (Chap. 2)", "url": "https://pensertransports.simdif.com/le_projet_lyon_turin_chapitrre_2.html", "contenu": "tunneliers, géologie, financement européen, opposition, tunnel de base, fret transalpin"},
    {"nom": "Liaison Seine-Nord", "url": "https://pensertransports.simdif.com/la_liaison_seine_nord.html", "contenu": "canal, fluvial, grand gabarit, report modal, logistique eau, ports"},
    {"nom": "Prévisions de transport", "url": "https://pensertransports.simdif.com/les_prévisions_de_transport.html", "contenu": "modélisation, trafic futur, statistiques, croissance, scénarios"},
    {"nom": "Évaluation des politiques", "url": "https://pensertransports.simdif.com/l’évaluation_des_politiques_et_des_projets_publics.html", "contenu": "socio-économie, rentabilité, utilité publique, calcul économique, bilan"},
    {"nom": "Questions sociales", "url": "https://pensertransports.simdif.com/les_questions_sociales.html", "contenu": "emploi, conditions de travail, syndicats, grèves, formation, retraites"},
    {"nom": "Europe des transports", "url": "https://pensertransports.simdif.com/l’europe_des_transports.html", "contenu": "paquet ferroviaire, bruxelles, directives, concurrence, ciel unique"},
    {"nom": "Fret ferroviaire", "url": "https://pensertransports.simdif.com/le_fret_ferroviaire.html", "contenu": "sncf, trains de marchandises, embranchements, wagon isolé, déclin"},
    {"nom": "Transport routier", "url": "https://pensertransports.simdif.com/le_transport_routier.html", "contenu": "camions, pavillon français, prix du gasoil, taxes, autoroutes"},
    {"nom": "Exemple Suisse", "url": "https://pensertransports.simdif.com/l’exemple_suisse.html", "contenu": "transit, alpes, redevance poids-lourds, intégration rail-route"},
    {"nom": "Politiques de voisinage", "url": "https://pensertransports.simdif.com/les_politiques_de_voisinage.html", "contenu": "coopération transfrontalière, intermodalité, zones urbaines"},
    {"nom": "Territoires & Démocratie", "url": "https://pensertransports.simdif.com/territoires,_transports,_et_démocratie.html", "contenu": "gilets jaunes, décentralisation, concertation, fracture territoriale"},
    {"nom": "Mesurer le fret", "url": "https://pensertransports.simdif.com/mesurer_les_transports_de_fret.html", "contenu": "tonnes-kilomètres, indicateurs, comptages, flux de marchandises"},
    {"nom": "Tarification infrastructures", "url": "https://pensertransports.simdif.com/la_tarification_des_infrastructures.html", "contenu": "péages, redevances, coût marginal, usager-payeur"},
    {"nom": "Débat Politiques Publiques", "url": "https://pensertransports.simdif.com/débat_général_sur_les_politiques_publiques.html", "contenu": "élection, programmes, débat public, orientations"},
    {"nom": "Prospective (OEST)", "url": "https://pensertransports.simdif.com/fin_de_l_administration_prospective_et_de_l_aventure_de_l_oest.html", "contenu": "histoire, administration, recherche, ministère, planification"},
    {"nom": "Incompréhension des enjeux", "url": "https://pensertransports.simdif.com/la_lente_incompréhension_des_enjeux.html", "contenu": "crise, analyse, prospective défaillante, erreurs"},
    {"nom": "Empires et Réseaux", "url": "https://pensertransports.simdif.com/les_empires_et_les_réseaux.html", "contenu": "géopolitique, puissance, flux mondiaux, logistique globale"},
    {"nom": "Mobilité militaire (UE)", "url": "https://pensertransports.simdif.com/mobilité_militaire_et_union_européenne_dialogue_de_sourds_.html", "contenu": "défense, otan, infrastructures stratégiques, corridors"},
    {"nom": "Origine des corridors", "url": "https://pensertransports.simdif.com/a_l_origine_des_corridors.html", "contenu": "ten-t, réseaux transeuropéens, axes prioritaires, histoire"}
]

data = []
glossary = {}

if os.path.exists(glossary_file):
    try:
        with open(glossary_file, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
    except: pass

try:
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        reader.fieldnames = [name.strip().upper() for name in reader.fieldnames]
        for row in reader:
            t = row.get('TITRE', '').strip()
            d = row.get('DATE', '').strip()
            u = row.get('URL', '').strip()
            k = row.get('KEYWORDS', '').strip()
            year_match = re.search(r'(19|20)\d{2}', d + " " + t)
            year = int(year_match.group()) if year_match else 0
            data.append({'url': u, 'title': t, 'keywords': k, 'date': d, 'year': year})

    data.sort(key=lambda x: x['year'], reverse=True)

    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bibliothèque Patrice Salini</title>
    <style>
        :root { --accent: #0056b3; --video: #059669; }
        body { margin: 0; font-family: system-ui, sans-serif; background: #f1f5f9; height: 100vh; display: flex; flex-direction: column; }
        header { background: white; padding: 10px; text-align: center; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
        h1 { margin: 0 0 8px 0; font-size: 1.4em; color: #1e3a8a; }
        .nav-sites { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-bottom: 5px; }
        .nav-sites a { text-decoration: none; color: var(--accent); font-weight: bold; font-size: 0.7em; padding: 4px 8px; background: #f1f5f9; border-radius: 4px; border: 1px solid #e2e8f0; }
        
        .wrapper { display: flex; flex-grow: 1; overflow: hidden; padding: 10px; gap: 10px; }
        .sidebar { width: 280px; background: white; border-radius: 8px; display: flex; flex-direction: column; border: 1px solid #e2e8f0; }
        .main { flex-grow: 1; background: white; border-radius: 8px; display: flex; flex-direction: column; border: 1px solid #e2e8f0; overflow: hidden; }

        .search-area { padding: 10px; border-bottom: 1px solid #f1f5f9; display: flex; gap: 8px; align-items: center; }
        #search { flex-grow: 1; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e0; font-size: 16px; }
        .btn-sort { padding: 8px; background: #f1f5f9; border: 1px solid #cbd5e0; border-radius: 6px; cursor: pointer; font-size: 0.8em; white-space: nowrap; }

        #global-list, #focus-list { overflow-y: auto; padding: 10px; }
        .card { background: #f8fafc; margin-bottom: 8px; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
        .title { font-weight: bold; color: #1e3a8a; font-size: 0.9em; flex-grow: 1; }
        .date-tag { font-size: 0.75em; color: #64748b; background: #e2e8f0; padding: 2px 5px; border-radius: 4px; }
        .actions { display: flex; gap: 5px; }
        .btn { text-decoration: none; padding: 6px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8em; color: white; }
        .btn-view { background: var(--accent); }
        .btn-vid { background: var(--video); }
        .btn-dl { background: #64748b; }

        @media (max-width: 768px) {
            .wrapper { flex-direction: column; overflow-y: auto; }
            .sidebar { width: 100%; order: 2; height: auto; }
            .main { width: 100%; order: 1; height: auto; }
            body { height: auto; display: block; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Bibliothèque Patrice Salini</h1>
        <div class="nav-sites">
            <a href="https://pensertransports.simdif.com" target="_blank">Penser les Transports (P. Salini & C. Reynaud)</a>
            <a href="https://www.editions-harmattan.fr/catalogue/auteur/patrice-salini/15031" target="_blank">L'Harmattan</a>
            <a href="https://www.transportinfo.fr/?s=patrice+Salini" target="_blank">Transport Info</a>
            <a href="mailto:patrice.salini@wanadoo.fr">✉ Contact</a>
        </div>
    </header>

    <div class="wrapper">
        <main class="main">
            <div class="search-area">
                <input type="search" id="search" placeholder="Rechercher...">
                <button id="sortBtn" class="btn-sort" onclick="toggleSort()">▼ Récent</button>
            </div>
            <div id="counter" style="padding: 5px 10px; font-size: 0.7em; color: #94a3b8; font-weight: bold;"></div>
            <div id="global-list"></div>
        </main>
        <aside class="sidebar">
            <div style="padding:10px; font-weight:bold; color: #1e3a8a; border-bottom: 1px solid #f1f5f9;">Focus thématique</div>
            <div id="focus-list"></div>
        </aside>
    </div>

    <script>
        const docs = DOCS_PLACEHOLDER;
        const glossary = GLOSSARY_PLACEHOLDER;
        const onglets = ONGLETS_PLACEHOLDER;
        let currentDocs = [...docs];
        let isDesc = true;

        function toggleSort() {
            isDesc = !isDesc;
            document.getElementById('sortBtn').innerText = isDesc ? "▼ Récent" : "▲ Ancien";
            render();
        }

        function render() {
            const query = document.getElementById('search').value.toLowerCase().trim();
            let filtered = [...docs];
            
            if (query) {
                let terms = [query];
                if (glossary[query]) terms = [...terms, ...glossary[query].map(t => t.toLowerCase())];
                filtered = docs.filter(d => terms.some(t => (d.title + d.keywords).toLowerCase().includes(t)));
                
                const matchedOnglets = onglets.filter(o => terms.some(t => (o.nom + o.contenu).toLowerCase().includes(t)));
                document.getElementById('focus-list').innerHTML = matchedOnglets.map(o => `
                    <div style="background:#f0f9ff; padding:8px; border-radius:6px; margin-bottom:5px; border-left:3px solid #0369a1;">
                        <a href="${o.url}" target="_blank" style="text-decoration:none; color:#1e3a8a; font-weight:bold; font-size:0.8em;">${o.nom}</a>
                    </div>`).join('') || '<p style="text-align:center;font-size:0.7em;color:#94a3b8;">Aucun lien SimDif</p>';
            } else {
                document.getElementById('focus-list').innerHTML = '<p style="text-align:center;color:#94a3b8;font-size:0.75em;padding:10px;">Lien automatique SimDif (tapez un mot-clé).</p>';
            }

            filtered.sort((a, b) => isDesc ? b.year - a.year : a.year - b.year);
            document.getElementById('counter').innerText = filtered.length + " documents (Total: " + docs.length + ")";
            displayList(filtered);
        }

        function displayList(list) {
            document.getElementById('global-list').innerHTML = list.map(d => {
                const isVideo = ['.mp4', '.mov', '.avi'].some(ext => d.url.toLowerCase().endsWith(ext));
                return `
                <div class="card">
                    <div style="flex-grow:1">
                        <span class="title">${d.title}</span>
                        <span class="date-tag">${d.date}</span>
                    </div>
                    <div class="actions">
                        <a href="${encodeURI(d.url)}" target="_blank" class="btn ${isVideo ? 'btn-vid':'btn-view'}">${isVideo ? '🎥' : '📄'}</a>
                        <a href="${encodeURI(d.url)}" download class="btn btn-dl">💾</a>
                    </div>
                </div>`;
            }).join('');
        }
        document.getElementById('search').addEventListener('input', render);
        window.onload = render;
    </script>
</body>
</html>"""

    final_html = html_content.replace('DOCS_PLACEHOLDER', json.dumps(data, ensure_ascii=False))
    final_html = final_html.replace('GLOSSARY_PLACEHOLDER', json.dumps(glossary, ensure_ascii=False))
    final_html = final_html.replace('ONGLETS_PLACEHOLDER', json.dumps(ONGLETS_SIMDIF, ensure_ascii=False))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("✅ Index complet restauré (Tri + Mentions Auteurs + Suivi).")

except Exception as e:
    print(f"❌ Erreur : {e}")
