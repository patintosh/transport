// search.js — recherche floue avec Fuse.js
(function () {
  'use strict';

  const INDEX_URL = '/transport/index.json';
  const PAGE_SIZE = 12;

  const el = {
    q: document.getElementById('q'),
    btn: document.getElementById('search-btn'),
    results: document.getElementById('results'),
    info: document.getElementById('results-info'),
    prev: document.getElementById('prev'),
    next: document.getElementById('next'),
    pager: document.getElementById('pager'),
    pageInfo: document.getElementById('page-info')
  };

  let index = [];
  let fuse = null;
  let results = []; // tableau d'objets {item, score}
  let page = 1;

  function safeResolveUrl(path) {
    try { return new URL(path, location.origin).href; } catch (e) { return path || ''; }
  }

  async function loadIndex() {
    try {
      const r = await fetch(INDEX_URL, {cache: 'no-store'});
      if (!r.ok) throw new Error('HTTP ' + r.status);
      index = await r.json();
      index.forEach(i => i._resolvedUrl = safeResolveUrl(i.path || ''));
      console.log('index loaded, items:', index.length);

      // Construire Fuse
      const options = {
        includeScore: true,
        shouldSort: true,
        threshold: 0.35,          // sensibilité : 0.0 = exact, 1.0 = très permissif
        distance: 100,           // distance pour correspondance partielle
        minMatchCharLength: 2,
        keys: [
          { name: 'title', weight: 0.7 },
          { name: 'path', weight: 0.2 },
          { name: 'type', weight: 0.1 }
        ]
      };
      fuse = new Fuse(index, options);
    } catch (e) {
      console.error('Erreur chargement index:', e && e.message ? e.message : e);
      index = [];
    }
  }

  function renderResults() {
    el.results.innerHTML = '';
    if (!results || results.length === 0) {
      el.info.textContent = 'Aucun résultat';
      el.pager.hidden = true;
      return;
    }

    const start = (page - 1) * PAGE_SIZE;
    const pageItems = results.slice(start, start + PAGE_SIZE);

    pageItems.forEach(r => {
      const item = r.item || r; // compatibilité si on a des objets bruts
      const score = (typeof r.score === 'number') ? (r.score) : null;

      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = item._resolvedUrl || item.path || '#';
      a.textContent = item.title || item.path || 'Sans titre';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      li.appendChild(a);

      const meta = document.createElement('span');
      meta.className = 'meta';
      const parts = [];
      if (item.type) parts.push(item.type);
      if (score !== null) parts.push('pertinence: ' + (Math.max(0, 1 - score)).toFixed(2));
      meta.textContent = parts.join(' • ');
      li.appendChild(meta);

      el.results.appendChild(li);
    });

    el.info.textContent = `Affichage ${start + 1}–${Math.min(start + PAGE_SIZE, results.length)} sur ${results.length}`;
    el.pageInfo.textContent = `Page ${page} / ${Math.ceil(results.length / PAGE_SIZE)}`;
    el.pager.hidden = results.length <= PAGE_SIZE;
  }

  function doSearch(term) {
    const t = (term || '').trim();
    if (!t) {
      // pas de terme : afficher tout (tri alphabétique sur title)
      results = index.slice().sort((a,b) => {
        const A = (a.title||'').toLowerCase();
        const B = (b.title||'').toLowerCase();
        return A < B ? -1 : (A > B ? 1 : 0);
      }).map(it => ({ item: it, score: 0 }));
    } else {
      // recherche floue via Fuse
      const fuseRes = fuse.search(t);
      results = fuseRes.map(r => ({ item: r.item, score: r.score }));
    }
    page = 1;
    renderResults();
  }

  el.btn.addEventListener('click', () => doSearch(el.q.value));
  el.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(el.q.value); }
  });

  el.prev.addEventListener('click', () => { if (page > 1) { page--; renderResults(); } });
  el.next.addEventListener('click', () => { if (page * PAGE_SIZE < results.length) { page++; renderResults(); } });

  // initialisation
  loadIndex().then(() => {
    // affichage initial : tout index
    results = index.slice().map(it => ({ item: it, score: 0 }));
    renderResults();
  });

})();
