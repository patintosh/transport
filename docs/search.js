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
 // --- Extraire date depuis l'en-tête HTTP d'un PDF (Last-Modified)
async function tryExtractDateFromPdfHead(url) {
  try {
    const r = await fetch(url, { method: 'HEAD', cache: 'no-store' });
    if (!r.ok) return null;
    const lm = r.headers.get('last-modified');
    if (!lm) return null;
    const d = new Date(lm);
    return isNaN(d) ? null : d;
  } catch (e) {
    return null;
  }
}

// --- Heuristique : extraire date depuis le nom de fichier (fallback)
function parseDateFromFilename(path) {
  if (!path) return null;
  const re1 = /(\d{1,2})[.\-_\/](\d{1,2})[.\-_\/](\d{2,4})/;
  const re2 = /(\d{4})[.\-_\/](\d{1,2})[.\-_\/](\d{1,2})/;
  let m = path.match(re1);
  if (m) {
    let day = parseInt(m[1],10), month = parseInt(m[2],10)-1, year = parseInt(m[3],10);
    if (year < 100) year += (year <= 49 ? 2000 : 1900);
    const d = new Date(year, month, day);
    return isNaN(d) ? null : d;
  }
  m = path.match(re2);
  if (m) {
    const year = parseInt(m[1],10), month = parseInt(m[2],10)-1, day = parseInt(m[3],10);
    const d = new Date(year, month, day);
    return isNaN(d) ? null : d;
  }
  return null;
}

// --- Enrichir les PDF : HEAD (Last-Modified) puis fallback filename
async function enrichPdfDates({ maxConcurrent = 6, maxTotal = 100 } = {}) {
  const candidates = index.filter(it => !it._dateObj && (it.path || '').toLowerCase().endsWith('.pdf'));
  if (candidates.length === 0) return;
  const toProcess = candidates.slice(0, maxTotal);
  let i = 0;
  async function worker() {
    while (i < toProcess.length) {
      const idx = i++;
      const it = toProcess[idx];
      const url = it._resolvedUrl || it.path;
      let d = await tryExtractDateFromPdfHead(url);
      if (!d) d = parseDateFromFilename(url);
      if (d) it._dateObj = d;
    }
  }
  const workers = [];
  for (let k = 0; k < Math.min(maxConcurrent, toProcess.length); k++) workers.push(worker());
  await Promise.all(workers);
  console.log('enrichPdfDates: processed', toProcess.length);
}

// --- Parser de date dans le texte (P.S. JJ/MM/AA ou variantes)
function parseDateFromPS(text) {
  if (!text) return null;
  const re = /P\.?S\.?\s*[:\-–]?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/i;
  const m = text.match(re);
  if (!m) return null;
  let day = parseInt(m[1], 10);
  let month = parseInt(m[2], 10) - 1;
  let year = parseInt(m[3], 10);
  if (year < 100) year += (year <= 49 ? 2000 : 1900);
  const d = new Date(year, month, day);
  return isNaN(d) ? null : d;
}

// --- Tenter d'extraire la date depuis le début ou la fin d'un HTML
async function tryExtractDateFromHtml(url) {
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) return null;
    const text = await r.text();
    // chercher dans le début et la fin du document (performant)
    const head = text.slice(0, 1200);
    const tail = text.slice(-1200);
    return parseDateFromPS(tail) || parseDateFromPS(head);
  } catch (e) {
    return null;
  }
}

// --- Enrichir les HTML en cherchant P.S. JJ/MM/AA au début ou à la fin
async function enrichHtmlDates({ maxConcurrent = 6, maxTotal = 50 } = {}) {
  const candidates = index.filter(it => !it._dateObj && (it.path || '').toLowerCase().endsWith('.html'));
  if (candidates.length === 0) return;
  const toProcess = candidates.slice(0, maxTotal);
  let i = 0;
  async function worker() {
    while (i < toProcess.length) {
      const idx = i++;
      const it = toProcess[idx];
      const url = it._resolvedUrl || it.path;
      const d = await tryExtractDateFromHtml(url);
      if (d) it._dateObj = d;
    }
  }
  const workers = [];
  for (let k = 0; k < Math.min(maxConcurrent, toProcess.length); k++) workers.push(worker());
  await Promise.all(workers);
  console.log('enrichHtmlDates: processed', toProcess.length);
}


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
