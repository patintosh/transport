console.log("search.js chargé et exécuté");
// search.js — consommation d'un index.json enrichi, fallback HEAD pour PDF
(function () {
  'use strict';

  const INDEX_URL = 'index.json';
  const PAGE_SIZE = 12;
  const BASE_PATH = ''; // si ton site est servi depuis /transport/, mettre '/transport/'

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
  let results = [];
  let page = 1;

  function safeResolveUrl(path) {
    if (!path) return '';
    path = String(path).trim();
    try {
      const u = new URL(path);
      return u.href;
    } catch (e) {}
    if (path.startsWith('/')) return location.origin + encodeURI(path);
    const base = BASE_PATH || '';
    return location.origin + (base.endsWith('/') || base === '' ? base : base + '/') + encodeURI(path);
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, m => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
  }

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
      if (typeof r.score === 'number') parts.push('pertinence: ' + (Math.max(0, 1 - r.score)).toFixed(2));
      if (item.excerpt) parts.push(item.excerpt.slice(0, 120) + (item.excerpt.length > 120 ? '…' : ''));
      meta.textContent = parts.join(' • ');
      li.appendChild(meta);
      el.results.appendChild(li);
    });
    if (el.info) el.info.textContent = `Affichage ${start + 1}–${Math.min(start + PAGE_SIZE, results.length)} sur ${results.length}`;
    if (el.pageInfo) el.pageInfo.textContent = `Page ${page} / ${Math.ceil(results.length / PAGE_SIZE)}`;
    if (el.pager) el.pager.hidden = results.length <= PAGE_SIZE;
  }

  function doSearch(term) {
    const t = (term || '').trim();
    if (!t) {
      results = index.slice().sort((a,b) => {
        const A = (a.title||'').toLowerCase();
        const B = (b.title||'').toLowerCase();
        return A < B ? -1 : (A > B ? 1 : 0);
      }).map(it => ({ item: it, score: 0 }));
    } else {
      if (fuse) {
        const fuseRes = fuse.search(t);
        results = fuseRes.map(r => ({ item: r.item, score: r.score }));
      } else {
        const filtered = index.filter(it => {
          const s = (it.title || '') + ' ' + (it.excerpt || '') + ' ' + (it.path || '') + ' ' + (it.type || '');
          return s.toLowerCase().includes(t.toLowerCase());
        });
        results = filtered.map(it => ({ item: it, score: 0 }));
      }
    }
    page = 1;
    renderResults();
  }

  if (el.btn) el.btn.addEventListener('click', () => doSearch(el.q ? el.q.value : ''));
  if (el.q) el.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(el.q.value); }
  });
  if (el.prev) el.prev.addEventListener('click', () => { if (page > 1) { page--; renderResults(); } });
  if (el.next) el.next.addEventListener('click', () => { if (page * PAGE_SIZE < results.length) { page++; renderResults(); } });

  async function loadIndex() {
  try {
    const response = await fetch('index.json');
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    const data = await response.json();
    console.log('Index chargé avec', data.length, 'documents');
    return data;
  } catch (e) {
    console.error('Erreur chargement index:', e.message);
    return [];
  }
}

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

  async function tryExtractTitleFromHtml(url) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) return null;
      const text = await r.text();
      const tMatch = text.match(/<title[^>]*>([^<]+)<\/title>/i);
      if (tMatch && tMatch[1]) return tMatch[1].trim();
      const h1Match = text.match(/<h1[^>]*>([^<]+)<\/h1>/i);
      if (h1Match && h1Match[1]) return h1Match[1].trim();
      return null;
    } catch (e) { return null; }
  }
function tryExtractDateFromPdfHead(headers) {
  if (!headers || typeof headers.get !== 'function') {
    return null;
  }

  const lastMod = headers.get('last-modified');
  if (!lastMod) return null;

  try {
    return new Date(lastMod);
  } catch {
    return null;
  }
}

  async function enrichPdfDatesAndTitles({ maxConcurrent = 6, maxTotal = 100 } = {}) {
    const candidates = index.filter(it => (!it._dateObj || !it.title) && (it.path || '').toLowerCase().endsWith('.pdf'));
    if (candidates.length === 0) return;
    const toProcess = candidates.slice(0, maxTotal);
    let i = 0;
    async function worker() {
      while (i < toProcess.length) {
        const idx = i++;
        const it = toProcess[idx];
        const url = it._resolvedUrl || safeResolveUrl(it.path || '');
        if (!it._dateObj) {
          const headResp = await fetch(url, { method: 'HEAD' });
const d = tryExtractDateFromPdfHead(headResp.headers) || parseDateFromFilename(url);

          if (d) it._dateObj = d;
        }
        // title from filename fallback
        if (!it.title) {
          const fname = (it.path || '').split('/').pop() || '';
          it.title = decodeURIComponent(fname.replace(/[-_]/g, ' '));
        }
      }
    }
    const workers = [];
    for (let k = 0; k < Math.min(maxConcurrent, toProcess.length); k++) workers.push(worker());
    await Promise.all(workers);
  }

  async function enrichHtmlTitlesAndDates({ maxConcurrent = 6, maxTotal = 100 } = {}) {
    const candidates = index.filter(it => (!it.title || !it._dateObj) && (it.path || '').toLowerCase().endsWith('.html'));
    if (candidates.length === 0) return;
    const toProcess = candidates.slice(0, maxTotal);
    let i = 0;
    async function worker() {
      while (i < toProcess.length) {
        const idx = i++;
        const it = toProcess[idx];
        const url = it._resolvedUrl || safeResolveUrl(it.path || '');
        if (!it.title) {
          const t = await tryExtractTitleFromHtml(url);
          if (t) it.title = t;
        }
        if (!it._dateObj) {
          // chercher P.S. dans début/fin
          try {
            const r = await fetch(url, { cache: 'no-store' });
            if (r.ok) {
              const text = await r.text();
              const head = text.slice(0, 1200);
              const tail = text.slice(-1200);
              const re = /P\.?S\.?\s*[:\-–]?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/i;
              const m = tail.match(re) || head.match(re);
              if (m) {
                let day = parseInt(m[1],10), month = parseInt(m[2],10)-1, year = parseInt(m[3],10);
                if (year < 100) year += (year <= 49 ? 2000 : 1900);
                const d = new Date(year, month, day);
                if (!isNaN(d)) it._dateObj = d;
              }
            }
          } catch (e) {}
        }
      }
    }
    const workers = [];
    for (let k = 0; k < Math.min(maxConcurrent, toProcess.length); k++) workers.push(worker());
    await Promise.all(workers);
  }

  async function loadIndex() {
    try {
      const r = await fetch(INDEX_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      index = await r.json();
      index.forEach(i => {
        i._resolvedUrl = safeResolveUrl(i.path || '');
        if (i.date && typeof i.date === 'string') {
          const d = new Date(i.date);
          if (!isNaN(d)) i._dateObj = d;
        } else if (i.published && typeof i.published === 'string') {
          const d = new Date(i.published);
          if (!isNaN(d)) i._dateObj = d;
        }
      });

      // fallback client enrichments (lightweight). Prefer server-generated index.json.
      await enrichPdfDatesAndTitles({ maxConcurrent: 6, maxTotal: 100 });
      await enrichHtmlTitlesAndDates({ maxConcurrent: 6, maxTotal: 100 });

      // build Fuse if available and index has titles
      if (typeof Fuse !== 'undefined') {
        const options = {
          includeScore: true,
          shouldSort: true,
          threshold: 0.35,
          distance: 100,
          minMatchCharLength: 2,
          keys: [
            { name: 'title', weight: 0.8 },
            { name: 'excerpt', weight: 0.15 },
            { name: 'path', weight: 0.05 }
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

  loadIndex().then(() => {
    const pdfs = index.filter(it => (it.type || '').toLowerCase() === 'pdf');
    if (pdfs.length) {
      const withDate = pdfs.filter(it => it._dateObj);
      if (withDate.length) {
        results = withDate.slice().sort((a,b) => b._dateObj - a._dateObj).map(it => ({ item: it, score: 0 }));
      } else {
        results = pdfs.slice().reverse().map(it => ({ item: it, score: 0 }));
      }
    } else {
      const withDateAll = index.filter(it => it._dateObj);
      if (withDateAll.length) {
        results = index.slice().sort((a,b) => (b._dateObj || 0) - (a._dateObj || 0)).map(it => ({ item: it, score: 0 }));
      } else {
        results = index.slice().map(it => ({ item: it, score: 0 }));
      }
    }
    page = 1;
    renderResults();
    if (typeof renderLatestArticle === 'function') renderLatestArticle(true);
  });

  // expose for debugging
  window.__searchIndex = { getIndex: () => index, getResults: () => results };
})();
