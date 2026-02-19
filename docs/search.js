// ============================================================
//  SEARCH ENGINE FOR TRANSPORT DOCUMENTS — VERSION STABLE 2026
//  Updated: encode paths and robust URL resolution
// ============================================================

// ------------------------------
// URL RESOLUTION AND ENCODING
// ------------------------------
function normalizePath(path) {
  // If path already looks like an absolute URL, encode and return it
  try {
    const maybeUrl = new URL(path);
    return encodeURI(maybeUrl.href);
  } catch (e) {
    // Not an absolute URL: build a full URL relative to the current site base
    // Determine a sensible base: the directory of the current page (e.g., /transport/)
    const pageBase = window.location.origin + window.location.pathname.replace(/\/[^/]*$/, '/');
    // Remove any leading slash from path to avoid double slashes
    const clean = String(path).replace(/^\//, '');
    // Encode the path but preserve slashes between path segments
    const encoded = encodeURI(clean);
    return pageBase + encoded;
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
// LOAD INDEX.JSON
// ------------------------------
async function loadIndex() {
  // Try to fetch index.json relative to the current page first
  let indexUrl = './index.json';
  try {
    const resp = await fetch(indexUrl);
    if (!resp.ok) {
      // fallback to /index.json or /docs/index.json if needed
      const alt1 = '/index.json';
      const alt2 = './docs/index.json';
      const r1 = await fetch(alt1);
      if (r1.ok) indexUrl = alt1;
      else {
        const r2 = await fetch(alt2);
        if (r2.ok) indexUrl = alt2;
        else {
          // final fallback: try /transport/index.json (GitHub Pages user repo)
          const r3 = await fetch('/transport/index.json');
          if (r3.ok) indexUrl = '/transport/index.json';
          else {
            // if none found, throw to be handled by caller
            throw new Error('index.json not found');
          }
        }
      }
    }
  } catch (e) {
    // try a few common fallbacks synchronously
    const fallbacks = ['/index.json', './docs/index.json', '/transport/index.json'];
    let found = false;
    for (const f of fallbacks) {
      try {
        const r = await fetch(f);
        if (r.ok) {
          indexUrl = f;
          found = true;
          break;
        }
      } catch (err) { /* ignore */ }
    }
    if (!found) throw e;
  }

  const indexResp = await fetch(indexUrl);
  window.indexData = await indexResp.json();

  // Enrich entries with resolved, encoded URLs and try to get dates
  for (const it of window.indexData) {
    // Use the raw path from the index but build a normalized URL
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

  // Ensure Fuse is available
  if (typeof Fuse === 'undefined') {
    console.warn('Fuse.js not found. Search will not be fuzzy.');
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
    // simple fallback substring search
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
      // Use the already encoded _url; escape title for safety
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
    console.error('Failed to load index.json', e);
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
