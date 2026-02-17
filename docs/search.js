// search.js — recherche floue avec Fuse.js (fichier complet, prêt à coller)
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
  let results = []; // tableau d'objets { item, score }
  let page = 1;

  function safeResolveUrl(path) {
    try { return new URL(path, location.origin).href; } catch (e) { return path || ''; }
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, function (m) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]);
    });
  }

  // Retourne le "dernier" item selon priorité PDF puis date puis position
  function findLatest(preferPdf = true) {
    if (!index || index.length === 0) return null;

    if (preferPdf) {
      const pdfs = index.filter(it => (it.type || '').toLowerCase() === 'pdf');
      if (pdfs.length > 0) {
        const withDate = pdfs.filter(it => it._dateObj);
        if (withDate.length) {
          return withDate.slice().sort((a, b) => b._dateObj - a._dateObj)[0];
        }
        return pdfs[pdfs.length - 1];
      }
    }

    const withDate = index.filter(it => it._dateObj);
    if (withDate.length) {
      return withDate.slice().sort((a, b) => b._dateObj - a._dateObj)[0];
    }

    return index[index.length - 1];
  }

  // Affiche le dernier article dans le DOM (titre + bouton Lire)
  function renderLatestArticle(preferPdf = true) {
    const container = document.getElementById('latest-article');
    if (!container) return;
    const latest = findLatest(preferPdf);
    if (!latest) { container.innerHTML = ''; return; }

    const url = latest._resolvedUrl || latest.path || '#';
    const title = latest.title || latest.path || 'Sans titre';
    const dateVal = latest.date || latest.published || latest.created;
    const dateHtml = dateVal ? `<time class="meta">${new Date(dateVal).toLocaleDateString()}</time>` : '';

    container.innerHTML = `
      <div class="latest-card">
        <div class="latest-left">
          <strong class="latest-label">Dernier article</strong>
          <a class="latest-title" href="${url}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>
          <div class="latest-meta">${dateHtml}</div>
        </div>
        <div class="latest-action">
          <a class="btn-primary" href="${url}" target="_blank" rel="noopener noreferrer">Lire</a>
        </div>
      </div>
    `;
  }

  // Rendu des résultats (utilise la variable globale `results` qui contient {item, score})
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
      const item = r.item || r;
      const score = (typeof r.score === 'number') ? r.score : null;

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

  // Recherche (utilise Fuse si disponible, sinon filtre simple)
  function doSearch(term) {
    const t = (term || '').trim();
    if (!t) {
      // pas de terme : afficher tout (tri alphabétique sur title)
      results = index.slice().sort((a, b) => {
        const A = (a.title || '').toLowerCase();
        const B = (b.title || '').toLowerCase();
        return A < B ? -1 : (A > B ? 1 : 0);
      }).map(it => ({ item: it, score: 0 }));
    } else {
      if (fuse) {
        const fuseRes = fuse.search(t);
        results = fuseRes.map(r => ({ item: r.item, score: r.score }));
      } else {
        // fallback : recherche simple contains sur title/path/type
        const filtered = index.filter(it => {
          const s = (it.title || '') + ' ' + (it.path || '') + ' ' + (it.type || '');
          return s.toLowerCase().includes(t.toLowerCase());
        });
        results = filtered.map(it => ({ item: it, score: 0 }));
      }
    }
    page = 1;
    renderResults();
  }

  // Écouteurs d'événements pour le formulaire et la pagination
  el.btn && el.btn.addEventListener('click', () => doSearch(el.q.value));
  el.q && el.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(el.q.value); }
  });
  el.prev && el.prev.addEventListener('click', () => { if (page > 1) { page--; renderResults(); } });
  el.next && el.next.addEventListener('click', () => { if (page * PAGE_SIZE < results.length) { page++; renderResults(); } });

  // Chargement de l'index et initialisation
  async function loadIndex() {
    try {
      const r = await fetch(INDEX_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      index = await r.json();

      // Résoudre les URLs et normaliser les dates
      index.forEach(i => {
        i._resolvedUrl = safeResolveUrl(i.path || '');
        if (i.date && typeof i.date === 'string') {
          const d = new Date(i.date);
          if (!isNaN(d)) i._dateObj = d;
        } else if (i.published && typeof i.published === 'string') {
          const d = new Date(i.published);
          if (!isNaN(d)) i._dateObj = d;
        } else if (i.created && typeof i.created === 'string') {
          const d = new Date(i.created);
          if (!isNaN(d)) i._dateObj = d;
        }
      });

      // Construire Fuse si disponible
      if (typeof Fuse !== 'undefined') {
        const options = {
          includeScore: true,
          shouldSort: true,
          threshold: 0.35,
          distance: 100,
          minMatchCharLength: 2,
          keys: [
            { name: 'title', weight: 0.7 },
            { name: 'path', weight: 0.2 },
            { name: 'type', weight: 0.1 }
          ]
        };
        fuse = new Fuse(index, options);
      } else {
        fuse = null;
      }

      console.log('index loaded, items:', index.length);
    } catch (e) {
      console.error('Erreur chargement index:', e && e.message ? e.message : e);
      index = [];
      fuse = null;
    }
  }

  // initialisation après chargement
  loadIndex().then(() => {
    // Priorité aux PDF pour l'affichage initial
    const pdfs = index.filter(it => (it.type || '').toLowerCase() === 'pdf');
    if (pdfs.length) {
      const withDate = pdfs.filter(it => it._dateObj);
      if (withDate.length) {
        results = withDate.slice().sort((a, b) => b._dateObj - a._dateObj).map(it => ({ item: it, score: 0 }));
      } else {
        results = pdfs.slice().reverse().map(it => ({ item: it, score: 0 }));
      }
    } else {
      const withDateAll = index.filter(it => it._dateObj);
      if (withDateAll.length) {
        results = index.slice().sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0)).map(it => ({ item: it, score: 0 }));
      } else {
        results = index.slice().map(it => ({ item: it, score: 0 }));
      }
    }

    page = 1;
    renderResults();
    renderLatestArticle(true);
  });

})();
