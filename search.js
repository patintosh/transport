// ============================================================
//  SEARCH ENGINE FOR TRANSPORT DOCUMENTS — VERSION STABLE 22 fev 2026
// ============================================================

// ------------------------------
// URL RESOLUTION AND ENCODING
// ------------------------------
function normalizePath(path) {
  try {
    const maybeUrl = new URL(path);
    return encodeURI(maybeUrl.href);
  } catch (e) {
    const pathname = window.location.pathname;
    const match = pathname.match(/^\/[^/]+\/?/);
    const repoBase = match ? match[0] : '/';
    const clean = String(path).replace(/^\//, '');
    const encoded = encodeURI(clean);
    return window.location.origin + repoBase + encoded;
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

  // Chemin ABSOLU, toujours correct sur GitHub Pages
  const indexUrl = '/transport/index.json';

  const indexResp = await fetch(indexUrl, { cache: 'no-store' });
  if (!indexResp.ok) {
    throw new Error('Impossible de charger index.json: ' + indexResp.status);
  }

  window.indexData = await indexResp.json();

  // enrichissement (SANS HEAD → plus de CORS)
  for (const it of window.indexData) {
    const url = normalizePath(it.path);

    const d = parseDateFromFilename(it.path);
    if (d) it._dateObj = d;

    it._url = url;
  }

  const fuseOptions = {
    keys: ['title', 'path'],
    threshold: 0.3,
    includeScore: true
  };

  window.fuse = typeof Fuse === 'undefined'
    ? null
    : new Fuse(window.indexData, fuseOptions);
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

  // *** INPUT COMPATIBLE AVEC LES DEUX PAGES ***
  const input = document.getElementById('q') || document.getElementById('search');
  if (!input) return;

  // Recherche en tapant
  input.addEventListener('input', () => {
    const q = input.value;
    results = performSearch(q);
    renderResults(results);
  });

  // Bouton Rechercher (page d'accueil)
  const btn = document.getElementById('search-btn');
  if (btn) {
    btn.addEventListener('click', () => {
      const q = input.value;
      results = performSearch(q);
      renderResults(results);
    });
  }

  // Résultats initiaux
  results = performSearch('');
  renderResults(results);
});
