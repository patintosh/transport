import csv, json, re, os

csv_file = 'INVENTAIRE_CLEAN.csv'
glossary_file = 'glossaireinverse.json'
output_file = 'index.html'

# Index sémantique enrichi pour la fouille profonde du Focus
ONGLETS_SIMDIF = [
    {"nom": "Politique des transports", "url": "https://pensertransports.simdif.com/où_est_passée_la_politique_des_transports.html", "contenu": "stratégie nationale, planification, investissement, infrastructures, grands projets"},
    {"nom": "Lyon-Turin (Chap. 2)", "url": "https://pensertransports.simdif.com/le_projet_lyon_turin_chapitrre_2.html", "contenu": "tunneliers, géologie, financement européen, opposition, tunnel de base, fret transalpin"},
    {"nom": "Liaison Seine-Nord", "url": "https://pensertransports.simdif.com/la_liaison_seine_nord.html", "contenu": "canal, fluvial, grand gabarit, report modal, logistique eau, ports"},
    {"nom": "Prévisions de transport", "url": "https://pensertransports.simdif.com/les_prévisions_de_transport.html", "contenu": "modélisation, trafic futur, statistiques, croissance, scénarios"},
    {"nom": "Évaluation des politiques", "url": "https://pensertransports.simdif.com/l’évaluation_des_politiques_et_des_projets_publics.html", "contenu": "socio-économie, rentabilité, utilité publique, calcul économique, bilan"},
    {"nom": "Questions sociales", "url": "https://pensertransports.simdif.com/les_questions_sociales.html", "contenu": "emploi, conditions de travail, syndicats, grèves, formation, retraites"},
    {"nom": "Europe des transports", "url": "https://pensertransports.simdif.com/l’europe_des_transports.html", "contenu": "paquet ferroviaire, bruxelles, directives, concurrence, ciel unique"},
    {"nom": "Fret ferroviaire", "url": "https://pensertransports.simdif.com/le_fret_ferroviaire.html", "contenu": "sncf, trains de marchandises, embranchements, wagon isolé, déclin, rail"},
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
    json_docs = json.dumps(data, ensure_ascii=False)
    json_glossary = json.dumps(glossary, ensure_ascii=False)
    json_onglets = json.dumps(ONGLETS_SIMDIF, ensure_ascii=False)

    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Bibliothèque Numérique Patrice Salini</title>
    <style>
        :root { --glass: rgba(255, 255, 255, 0.85); --accent: #0056b3; }
        body { 
            margin: 0; font-family: 'Segoe UI', system-ui, sans-serif; 
            background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 100%);
            height: 100vh; display: flex; flex-direction: column; color: #1e293b;
        }
        header { 
            background: var(--glass); backdrop-filter: blur(12px);
            padding: 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.4);
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        .nav-sites { display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 15px; }
        .nav-sites a { 
            text-decoration: none; color: var(--accent); font-weight: bold; font-size: 0.85em;
            padding: 8px 16px; background: white; border-radius: 50px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s;
        }
        .nav-sites a:hover { background: var(--accent); color: white; }
        .nav-sites a.contact { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e0; }
        .nav-sites a.contact:hover { background: #475569; color: white; }

        .wrapper { display: flex; flex-grow: 1; overflow: hidden; padding: 20px; gap: 20px; }
        .sidebar { 
            width: 380px; background: var(--glass); backdrop-filter: blur(12px);
            border-radius: 20px; display: flex; flex-direction: column;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1); border: 1px solid rgba(255,255,255,0.4);
        }
        .main { 
            flex-grow: 1; background: var(--glass); backdrop-filter: blur(12px);
            border-radius: 20px; display: flex; flex-direction: column;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1); border: 1px solid rgba(255,255,255,0.4);
        }

        .search-area { padding: 20px; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; gap: 10px; }
        #search { flex-grow: 1; padding: 12px 20px; border-radius: 12px; border: 1px solid #cbd5e0; outline: none; background: rgba(255,255,255,0.5); }
        .btn-sort { padding: 10px 15px; border-radius: 12px; border: 1px solid #cbd5e0; background: white; cursor: pointer; font-weight: bold; }

        #global-list, #focus-list { overflow-y: auto; padding: 10px 20px; }
        
        .onglet-card {
            background: #e0f2fe; padding: 15px; border-radius: 12px; margin-bottom: 12px;
            border-left: 5px solid #0369a1; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .onglet-card a { text-decoration: none; color: #1e3a8a; font-weight: bold; font-size: 0.9em; display: block; }

        .card { 
            background: rgba(255,255,255,0.7); margin-bottom: 12px; padding: 15px; border-radius: 12px;
            display: flex; justify-content: space-between; align-items: center; border: 1px solid white;
        }
        .tag { font-size: 0.7em; padding: 3px 8px; border-radius: 5px; background: #e0e7ff; color: #4338ca; font-weight: 700; margin-right: 5px; }
        .btn-consulter { background: var(--accent); color: white; text-decoration: none; padding: 10px 18px; border-radius: 10px; font-weight: bold; font-size: 0.85em; }
    </style>
</head>
<body>
    <header>
        <h1>Bibliothèque Numérique de Patrice Salini</h1>
        <div class="nav-sites">
            <a href="https://pensertransports.simdif.com" target="_blank">1. Penser les Transports</a>
            <a href="https://www.editions-harmattan.fr/catalogue/auteur/patrice-salini/15031" target="_blank">2. L'Harmattan</a>
            <a href="https://www.transportinfo.fr/?s=patrice+Salini" target="_blank">3. Transport Info</a>
            <a href="mailto:patrice.salini@wanadoo.fr" class="contact">✉ Me contacter</a>
        </div>
    </header>

    <div class="wrapper">
        <aside class="sidebar">
            <div style="padding:20px; font-weight:bold; color: #1e3a8a; border-bottom: 1px solid rgba(0,0,0,0.05);">Focus : Penser-Transport</div>
            <div id="focus-list"></div>
        </aside>

        <main class="main">
            <div class="search-area">
                <input type="text" id="search" placeholder="Recherche par concept, titre ou année...">
                <button class="btn-sort" onclick="toggleSort()">⇅ Date</button>
            </div>
            <div id="counter" style="padding: 0 20px 10px; font-size: 0.85em; font-weight: bold; color: #64748b;"></div>
            <div id="global-list"></div>
        </main>
    </div>

    <script>
        const docs = DOCS_PLACEHOLDER;
        const glossary = GLOSSARY_PLACEHOLDER;
        const onglets = ONGLETS_PLACEHOLDER;

        function toggleSort() { docs.reverse(); render(); }

        function render() {
            const query = document.getElementById('search').value.toLowerCase().trim();
            
            if (!query) {
                document.getElementById('focus-list').innerHTML = `
                    <div style="padding:20px; text-align:center; color:#64748b;">
                        <p style="font-size:0.9em;">Explorez la base documentaire par mots-clés pour voir les analyses liées du site <strong>Penser-Transport</strong>.</p>
                    </div>`;
                document.getElementById('counter').innerText = "Dernières publications (15 documents)";
                displayList(docs.slice(0, 15));
                return;
            }

            let terms = [query];
            if (glossary[query]) terms = [...terms, ...glossary[query].map(t => t.toLowerCase())];

            // FOCUS : Analyse SimDif par contenu
            const matchedOnglets = onglets.filter(o => {
                const searchArea = (o.nom + o.contenu + o.url).toLowerCase();
                return terms.some(t => searchArea.includes(t));
            });

            document.getElementById('focus-list').innerHTML = matchedOnglets.length ? matchedOnglets.map(o => `
                <div class="onglet-card">
                    <a href="${o.url}" target="_blank">${o.nom}</a>
                    <div style="font-size:0.75em; color:#0369a1; margin-top:5px; font-style:italic;">Page SimDif correspondante</div>
                </div>
            `).join('') : '<p style="padding:20px; color:#94a3b8; font-size:0.8em; text-align:center;">Aucune page spécifique sur le site pour ce concept.</p>';

            // LISTE PDF
            const filtered = docs.filter(d => {
                const text = (d.title + d.keywords).toLowerCase();
                return terms.some(t => text.includes(t));
            });
            document.getElementById('counter').innerText = filtered.length + " documents identifiés";
            displayList(filtered);
        }

        function displayList(list) {
            document.getElementById('global-list').innerHTML = list.map(d => `
                <div class="card">
                    <div style="flex-grow:1; padding-right:20px;">
                        <span style="font-weight:bold; display:block; color:#1e3a8a;">${d.title}</span>
                        <span class="tag">${d.date}</span>
                    </div>
                    <a href="${encodeURI(d.url)}" target="_blank" class="btn-consulter">PDF</a>
                </div>
            `).join('');
        }

        document.getElementById('search').addEventListener('input', render);
        window.onload = render;
    </script>
</body>
</html>"""

    final_html = html_content.replace('DOCS_PLACEHOLDER', json_docs).replace('GLOSSARY_PLACEHOLDER', json_glossary).replace('ONGLETS_PLACEHOLDER', json_onglets)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("✅ Version finale générée : Liens sites + Contact + Accueil dynamique + Focus sémantique.")

except Exception as e:
    print(f"❌ Erreur : {e}")
