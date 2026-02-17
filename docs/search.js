// search.js — recherche floue avec Fuse.js (remplacer entièrement le fichier existant)
(function () {
  'use strict';

  const INDEX_URL = '/transport/index.json'; // adapte si nécessaire
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
  if (!path) return '';
  path = String(path).trim();
  // URL absolue
  try {
    const u = new URL(path);
    return u.href;
  } catch (e) { /* pas une URL absolue */ }

  // chemin absolu sur le site (commence par /)
  if (path.startsWith('/')) {
    return location.origin + encodeURI(path);
  }

  // chemin relatif : base sur la racine du site ou sur le dossier courant
  // si ton site est servi depuis /transport/ (GitHub Pages docs/), ajuste BASE_PATH
  const BASE_PATH = '/transport/'; // <-- adapte si nécessaire, ou '' si index.json à la racine
  return location.origin + (BASE_PATH.endsWith('/') ? BASE_PATH : BASE_PATH + '/') + encodeURI(path);
}


  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, function (m) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]);
    });
  }

  // --- findLatest (priorité PDF puis date puis position)
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

  // --- renderLatestArticle (titre + bouton Lire)
  function renderLatestArticle(preferPdf = true) {
    const container = document.getElementById('latest-article');
    if (!container) return;
    const latest = findLatest(preferPdf);
    if (!latest) { container.innerHTML = ''; return; }

    const url = latest._resolvedUrl || latest.path || '#';
    const title = latest.title || latest.path || 'Sans titre';
    const dateVal = latest.date || latest.published || latest.created || (latest._dateObj ? latest._dateObj.toISOString() : '');
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

  // --- renderResults
  function renderResults() {
    if (!el.results) return;
    el.results.innerHTML = '';
    if (!results || results.length === 0) {
      if (el.info) el.info.textContent = 'Aucun résultat';
      if (el.pager) el.pager.hidden = true;
      return;
    }

    const start = (page - 1) * PAGE_SIZE;
    const pageItems = results.slice(start, start + PAGE_SIZE);

    pageItems.forEach(r => {
      const item = r.item || r;
      const score = (typeof r.score === 'number') ? r.score : null;

      const li = document.createElement('li');
      li.className = 'result-item';

      const a = document.createElement('a');
      a.href = item._resolvedUrl || item.path || '#';
      a.textContent = item.title || item.path || 'Sans titre';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.className = 'result-link';
      li.appendChild(a);

      const meta = document.createElement('div');
      meta.className = 'result-meta';
      const parts = [];
      if (item.type) parts.push(item.type);
      if (item._dateObj) parts.push(new Date(item._dateObj).toLocaleDateString());
      if (score !== null) parts.push('pertinence: ' + (Math.max(0, 1 - score)).toFixed(2));
      meta.textContent = parts.join(' • ');
      li.appendChild(meta);

      el.results.appendChild(li);
    });

    if (el.info) el.info.textContent = `Affichage ${start + 1}–${Math.min(start + PAGE_SIZE, results.length)} sur ${results.length}`;
    if (el.pageInfo) el.pageInfo.textContent = `Page ${page} / ${Math.ceil(results.length / PAGE_SIZE)}`;
    if (el.pager) el.pager.hidden = results.length <= PAGE_SIZE;
  }

  // --- doSearch
  function doSearch(term) {
    const t = (term || '').trim();
    if (!t) {
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
        const filtered = index.filter(it => {
          const s = (it.title || '') + ' ' + (it.path || '') + ' ' + (it.type || '') + ' ' + (it.excerpt || '');
          return s.toLowerCase().includes(t.toLowerCase());
        });
        results = filtered.map(it => ({ item: it, score: 0 }));
      }
    }
    page = 1;
    renderResults();
  }

  // --- listeners (defensive)
  if (el.btn) el.btn.addEventListener('click', () => doSearch(el.q ? el.q.value : ''));
  if (el.q) el.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(el.q.value); }
  });
  if (el.prev) el.prev.addEventListener('click', () => { if (page > 1) { page--; renderResults(); } });
  if (el.next) el.next.addEventListener('click', () => { if (page * PAGE_SIZE < results.length) { page++; renderResults(); } });

  // --- helpers pour extraction de date

  // try HEAD Last-Modified for PDFs
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

  // parse date from filename
  function parseDateFromFilename(path) {
    if (!path) return null;
    const re1 = /(\d{1,2})[.\-_\/](\d{1,2})[.\-_\/](\d{2,4})/;
    const re2 = /(\d{4})[.\-_\/](\d{1,2})[.\-_\/](\d{1,2})/;
    let m = path.match(re1);
    if (m) {
      let day = parseInt(m[1], 10), month = parseInt(m[2], 10) - 1, year = parseInt(m[3], 10);
      if (year < 100) year += (year <= 49 ? 2000 : 1900);
      const d = new Date(year, month, day);
      return isNaN(d) ? null : d;
    }
    m = path.match(re2);
    if (m) {
      const year = parseInt(m[1], 10), month = parseInt(m[2], 10) - 1, day = parseInt(m[3], 10);
      const d = new Date(year, month, day);
      return isNaN(d) ? null : d;
    }
    return null;
  }

  // parse P.S. date in text
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

  // try extract date from HTML (head or tail)
  async function tryExtractDateFromHtml(url) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) return null;
      const text = await r.text();
      const head = text.slice(0, 1200);
      const tail = text.slice(-1200);
      return parseDateFromPS(tail) || parseDateFromPS(head);
    } catch (e) {
      return null;
    }
  }

  // enrich PDFs via HEAD + filename
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
  }

  // enrich HTML via P.S. detection
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
  }

  // --- loadIndex
  async function loadIndex() {
    try {
      const r = await fetch(INDEX_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      index = await r.json();

      // resolve urls and normalize existing dates
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

      // enrich dates: PDFs first, then HTML (await to ensure correct sorting)
      await enrichPdfDates({ maxConcurrent: 6, maxTotal: 100 });
      await enrichHtmlDates({ maxConcurrent: 6, maxTotal: 50 });
// récupère le <title> ou premier <h1> d'une page HTML (limité, respect CORS)
async function fetchTitleFromHtml(url) {
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) return null;
    const text = await r.text();
    // chercher <title>
    const tMatch = text.match(/<title[^>]*>([^<]+)<\/title>/i);
    if (tMatch && tMatch[1]) return tMatch[1].trim();
    // fallback : premier <h1>
    const h1Match = text.match(/<h1[^>]*>([^<]+)<\/h1>/i);
    if (h1Match && h1Match[1]) return h1Match[1].trim();
    return null;
  } catch (e) {
    return null;
  }
}

// enrichir les items sans title (concurrence limitée)
async function enrichTitles({ maxConcurrent = 6, maxTotal = 50 } = {}) {
  const candidates = index.filter(it => !(it.title) && (it.path || '').toLowerCase().endsWith('.html'));
  if (candidates.length === 0) return;
  const toProcess = candidates.slice(0, maxTotal);
  let i = 0;
  async function worker() {
    while (i < toProcess.length) {
      const idx = i++;
      const it = toProcess[idx];
      const url = it._resolvedUrl || safeResolveUrl(it.path || '');
      const t = await fetchTitleFromHtml(url);
      if (t) it.title = t;
    }
  }
  const workers = [];
  for (let k = 0; k < Math.min(maxConcurrent, toProcess.length); k++) workers.push(worker());
  await Promise.all(workers);
  console.log('enrichTitles: done', toProcess.length);
}

      // build Fuse if available
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
    // initial results: priorité aux PDF si présents
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
