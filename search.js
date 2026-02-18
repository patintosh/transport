// ============================================================
//  SEARCH ENGINE FOR TRANSPORT DOCUMENTS
// ============================================================

// ------------------------------
// URL RESOLUTION
// ------------------------------
function safeResolveUrl(path) {
  if (!path) return '';
  path = String(path).trim();

  // Si path est déjà une URL absolue
  try {
    const u = new URL(path);
    return u.href;
  } catch (e) {
    // Sinon → chemin relatif tel qu'il apparaît dans index.json
    return '/' + path.replace(/^\//, '');
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
let index = [];
let fuse = null;
let results = [];
let page = 1;

// ------------------------------
// LOAD INDEX.JSON
// ------------------------------
async function loadIndex() {
  const resp = await fetch('/index.json');
  index = await resp.json();

  // Prépare les champs internes
  for (const it of index) {
    const url = safeResolveUrl(it.path);

    // Extraction date
    if (!it._dateObj) {
      try {
        const headResp = await fetch(url, { method: 'HEAD' });
        const d =
          tryExtractDateFromPdfHead(headResp.headers) ||
          parseDateFromFilename(url);
        if (d) it._dateObj = d;
      } catch (e) {
        const d = parseDateFromFilename(url);
        if (d) it._dateObj = d;
      }
    }

    // URL finale
    it._url = url;
  }

  // Fuse.js
  fuse = new Fuse(index, {
    keys: ['title', 'path'],
    threshold: 0.3,
    includeScore: true
  });
}

// ------------------------------
// PERFORM SEARCH
// ------------------------------
function performSearch(q) {
  if (!fuse) return [];

  if (!q || !q.trim()) {
    return index
      .slice()
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  const r = fuse.search(q.trim());
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
      const date = it._dateObj
        ? it._dateObj.getFullYear()
        : '';
      return `
        <div class="result">
          <a href="${escapeHtml(it._url)}" target="_blank">
            ${escapeHtml(it.title)}
          </a>
          <span class="date">${date}</span>
        </div>
      `;
    })
    .join('');
}

// ------------------------------
// INIT
// ------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  await loadIndex();

  const input = document.getElementById('search');
  if (!input) return;

  input.addEventListener('input', () => {
    const q = input.value;
    results = performSearch(q);
    renderResults(results);
  });

  // Affiche tout au début
  results = performSearch('');
  renderResults(results);
});
