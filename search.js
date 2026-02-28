// ============================================================
//  MOTEUR DE RECHERCHE — VERSION FINALE NETTOYÉE
// ============================================================

let DATA = [];
let GLOSSAIRE = {};
let SORT_MODE = "recent"; 

function normalizePath(path) {
  if (!path) return "#";
  if (path.startsWith('http')) return path;
  return path.trim(); 
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, m => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[m]));
}

function extractDate(it) {
  if (!it.date) return null;
  const raw = String(it.date).trim().toLowerCase();
  let mYear = raw.match(/(\d{4})/);
  if (mYear) return new Date(Number(mYear[1]), 0, 1);
  return null;
}

async function loadIndex() {
  const resp = await fetch("index.json");
  DATA = await resp.json();
}

async function loadGlossaire() {
  try {
    const resp = await fetch("glossaireinverse.json");
    GLOSSAIRE = await resp.json();
  } catch (e) {
    GLOSSAIRE = {};
  }
}

function performSearch(query) {
  const rawQ = query.trim().toLowerCase();
  if (!rawQ) return DATA;

  const searchTerms = rawQ.replace(/-/g, ' ').split(/\s+/).filter(t => t.length > 0);
  const allPossibleTerms = searchTerms.map(term => {
    let variations = [term];
    if (GLOSSAIRE[term]) variations = variations.concat(GLOSSAIRE[term]);
    return variations;
  });

  return DATA.filter(item => {
    const content = `
      ${item.title || ''} 
      ${item.description || ''} 
      ${item.path || ''} 
      ${Array.isArray(item.keywords) ? item.keywords.join(' ') : (item.keywords || '')}
    `.toLowerCase().replace(/-/g, ' ');

    return allPossibleTerms.every(variations => {
      return variations.some(v => content.includes(v.toLowerCase()));
    });
  });
}

function applyDateSort(arr) {
  return arr.sort((a, b) => {
    const da = extractDate(a);
    const db = extractDate(b);
    if (!da) return 1;
    if (!db) return -1;
    return SORT_MODE === "recent" ? db - da : da - db;
  });
}

// --- FONCTION D'AFFICHAGE (STYLE GOOGLE COURT) ---
function renderResults(arr) {
  const container = document.getElementById("results");
  if (!container) return;

  if (arr.length === 0) {
    container.innerHTML = "<div class='no-results'>Aucun document trouvé.</div>";
    return;
  }

  container.innerHTML = arr.map(it => {
    // On limite la description à 200 caractères pour la clarté
    const snippet = it.description && it.description.length > 200 
      ? it.description.substring(0, 200) + "..." 
      : (it.description || "Consulter le document");

    return `
    <article class="result-item" style="margin-bottom: 1.5rem; border-bottom: 1px solid #eee; padding-bottom: 1rem; font-family: arial, sans-serif;">
      <div style="display: flex; align-items: baseline; gap: 8px;">
        <span style="font-size: 0.65rem; color: #0056b3; border: 1px solid #0056b3; padding: 1px 4px; border-radius: 3px; text-transform: uppercase; font-weight: bold;">
          ${it.type_doc || 'DOC'}
        </span>
        <h3 style="margin: 0; font-size: 1.15rem;">
          <a href="${normalizePath(it.path)}" target="_blank" style="color: #1a0dab; text-decoration: none;">
            ${escapeHtml(it.title || "Sans titre")}
          </a>
        </h3>
      </div>

      <p style="margin: 6px 0; color: #4d5156; font-size: 0.9rem; line-height: 1.4;">
        ${escapeHtml(snippet)}
      </p>

      <div style="font-size: 0.75rem; color: #006621;">
        ${it.date ? `<span>Publié en : ${escapeHtml(it.date)}</span>` : ''}
      </div>
    </article>
    `;
  }).join("");
}

function updateResults() {
  const input = document.getElementById("q");
  const q = input ? input.value : "";
  let filtered = performSearch(q);
  filtered = applyDateSort(filtered);
  renderResults(filtered);
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadIndex();
  await loadGlossaire();
  const input = document.getElementById("q");
  if (input) input.addEventListener("input", updateResults);

  const toggleBtn = document.getElementById("toggleSortDate");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      SORT_MODE = (SORT_MODE === "recent") ? "old" : "recent";
      toggleBtn.textContent = SORT_MODE === "recent" ? "Tri : récents → anciens" : "Tri : anciens → récents";
      updateResults();
    });
  }
  updateResults();
});