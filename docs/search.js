// ============================================================
//  SEARCH ENGINE FOR TRANSPORT DOCUMENTS — VERSION STABLE 2026
//  Updated for script located in docs/ — robust index resolution
// ============================================================

// ------------------------------
// URL RESOLUTION AND ENCODING
// ------------------------------
function normalizePath(path) {
  // If path is already an absolute URL, encode and return it
  try {
    const maybeUrl = new URL(path);
    return encodeURI(maybeUrl.href);
  } catch (e) {
    // Not an absolute URL: build a full URL relative to the site root or current page
    // Determine a sensible base: prefer site root (e.g., /transport/) if present in pathname
    const pathname = window.location.pathname; // e.g., /transport/docs/search.html
    // Try to detect repo base like /transport/
    const match = pathname.match(/^\/[^/]+\/?/);
    const repoBase = match ? match[0] : '/';
    // If the script lives in /transport/docs/, we want base to be /transport/
    const siteBase = pathname.includes('/docs/') ? pathname.split('/docs/')[0] + '/' : repoBase;
    // Remove leading slash from path to avoid double slashes
    const clean = String(path).replace(/^\//, '');
    // Encode the path but preserve slashes
    const encoded = encodeURI(clean);
    // Build final URL
    return window.location.origin + siteBase + encoded;
  }
}

// ------------------------------
// ESCAPE HTML
// ------------------------------
function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, m => ({
    '&':'&amp;',
    '<':'&lt;',
    '>':'&gt;',
    '"':'&quot;',
    "'":'&#39;'
  }[m]));
}

// ------------------------------
// DATE EXTRACTION
// ------------------------------
function tryExtractDateFromPdfHead(headers) {
  if (!headers) return null;
  const lm = headers.get('last-modified');
  if (!lm) return null;
  const d = new Date(lm);
  return isNaN(d.getTime()) ? null : d;
}

function parseDateFromFilename(path) {
  const m = String(path).match(/(\d{4})/);
  if (!m) return null;
  const d = new Date(Number(m[1]), 0, 1);
  return isNaN(d.getTime()) ? null : d;
}

// ------------------------------
// GLOBALS
// ------------------------------
window.indexData = [];
window.fuse = null;
let results = [];

// ------------------------------
// LOAD INDEX.JSON (robust for docs/ location)
// ------------------------------
async function loadIndex() {
  // Candidate locations to try, in order. Because this script runs from docs/,
  // try ./index.json, ../index.json, /index.json, /transport/index.json
  const candidates = [
    './index.json',
    '../index.json',
    '/index.json',
    '/transport/index.json',
    './docs/index.json'
  ];

  let indexUrl = null;
  for (const c of candidates) {
    try {
      const r = await fetch(c, { method: 'GET', cache: 'no-store' });
      if (r.ok) {
        indexUrl = c;
        break;
      }
    } catch (e) {
      // ignore and try next
    }
  }

  if (!indexUrl) {
    throw new Error('index.json introuvable aux emplacements attendus.');
  }

  const indexResp = await fetch(indexUrl, { cache: 'no-store' });
  if (!indexResp.ok) throw new Error('Impossible de charger index.json: ' + indexResp.status);
  window.indexData = await indexResp.json();

  // Enrich entries with resolved, encoded URLs and try to get dates
  for (const it of window.indexData) {
    // Build normalized URL from the raw path in the index
    const url = normalizePath(it.path);

    if (!it._dateObj) {
      try {
        // HEAD request to get last-modified if available
        const headResp = await fetch(url, { method: 'HEAD' });
        const d =
          tryExtractDateFromPdfHead(headResp.headers) ||
          parseDateFromFilename(it.path);
        if (d) it._dateObj = d;
      } catch (e) {
        // fallback to parsing filename
        const fallback = parseDateFromFilename(it.path);
        if (fallback) it._dateObj = fallback;
      }
    }

    it._url = url;
  }

  const fuseOptions = {
    keys: ['title', 'path'],
    threshold: 0.3,
    includeScore: true
  };

  if (typeof Fuse === 'undefined') {
    console.warn('Fuse.js non trouvé — utilisation d’un fallback de recherche simple.');
    window.fuse = null;
  } else {
    window.fuse = new Fuse(window.indexData, fuseOptions);
  }
}

// ------------------------------
// PERFORM SEARCH
// ------------------------------
function performSearch(q) {
  if (!window.indexData) return [];

  if (!q || !q.trim()) {
    return window.indexData
      .slice()
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  if (!window.fuse) {
    const term = q.trim().toLowerCase();
    return window.indexData
      .filter(it => (it.title || '').toLowerCase().includes(term) || (it.path || '').toLowerCase().includes(term))
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  const r = window.fuse.search(q.trim());
  return r
    .map(x => x.item)
    .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
}

// ------------------------------
// RENDER RESULTS
// ------------------------------
function renderResults(list) {
  const container = document.getElementById('results');
  if (!container) return;

  container.innerHTML = list
    .map(it => {
      const date = it._dateObj ? it._dateObj.getFullYear() : '';
      return `
        <div class="result">
          <a href="${escapeHtml(it._url)}" target="_blank" rel="noopener noreferrer">
            ${escapeHtml(it.title)}
          </a>
          <span class="date">${escapeHtml(date)}</span>
        </div>
      `;
    })
    .join('');
}

// ------------------------------
// INIT
// ------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadIndex();
  } catch (e) {
    console.error('Échec du chargement de index.json', e);
    const container = document.getElementById('results');
    if (container) container.innerHTML = '<div class="error">Index introuvable. Vérifie index.json.</div>';
    return;
  }

  const input = document.getElementById('search');
  if (!input) return;

  input.addEventListener('input', () => {
    const q = input.value;
    results = performSearch(q);
    renderResults(results);
  });

  // initial render
  results = performSearch('');
  renderResults(results);
});
