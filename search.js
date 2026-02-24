// ============================================================
//  SEARCH ENGINE — VERSION STABLE 24 fev 2026 — 12:10
//  Multi-termes + Pondération positionnelle + Highlight limité
// ============================================================


// ------------------------------
// URL RESOLUTION
// ------------------------------
function normalizePath(path) {
  try {
    const maybeUrl = new URL(path, window.location.href);
    return encodeURI(maybeUrl.href);
  } catch (e) {
    console.error("PATH INVALIDE :", path);
    return "#";
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
// DATE EXTRACTION — VERSION SÉCURISÉE
// ------------------------------
function extractDate(it) {
  if (!it.date) return null;

  const y = it.date.match(/\b(19|20)\d{2}\b/);
  if (!y) return null;

  const year = Number(y[0]);

  if (year < 1950 || year > 2025) return null;

  const d = new Date(year, 0, 1);
  return isNaN(d.getTime()) ? null : d;
}


// ------------------------------
// GLOBALS
// ------------------------------
window.indexData = [];
let GLOSSAIRE = {};
let results = [];


// ------------------------------
// LOAD INDEX.JSON
// ------------------------------
async function loadIndex() {
  const resp = await fetch("index.json", { cache: "no-store" });
  if (!resp.ok) throw new Error("index.json introuvable");

  window.indexData = await resp.json();

  for (const it of window.indexData) {
    it._url = normalizePath(it.path);
    it._dateObj = extractDate(it);
  }
}


// ------------------------------
// LOAD GLOSSAIRE
// ------------------------------
async function loadGlossaire() {
  try {
    const resp = await fetch("glossaire_fusionne.json", { cache: "no-store" });
    if (resp.ok) GLOSSAIRE = await resp.json();
  } catch (e) {
    console.warn("Glossaire non chargé");
  }
}


// ============================================================
//  EXPANSION MULTI-TERMES
// ============================================================
function expandQuery(q) {
  const base = q.trim().toLowerCase();
  const terms = new Set();

  if (!base) return [];

  // Expression complète
  terms.add(base);

  // Synonymes multi-termes
  if (GLOSSAIRE[base]) {
    for (const syn of GLOSSAIRE[base]) {
      terms.add(String(syn).toLowerCase());
    }
  }

  // Découpage en mots simples
  const words = base.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);
  for (const w of words) {
    terms.add(w);
    if (GLOSSAIRE[w]) {
      for (const syn of GLOSSAIRE[w]) {
        terms.add(String(syn).toLowerCase());
      }
    }
  }

  return Array.from(terms);
}


// ============================================================
//  PONDÉRATION POSITIONNELLE
// ============================================================
function scoreDocument(it, terms) {
  let score = 0;

  const title = (it.numero || it.title || "").toLowerCase();
  const desc = (it.description || "").toLowerCase();
  const path = (it.path || "").toLowerCase();
  const keywords = (it.keywords || []).join(" ").toLowerCase();

  const words = desc.split(/\s+/);
  const first200 = words.slice(0, 200).join(" ");
  const last200 = words.slice(-200).join(" ");

  for (const t of terms) {
    const re = new RegExp(`\\b${t}\\b`, "i");

    if (re.test(title)) score += 10;
    if (re.test(first200)) score += 6;
    if (re.test(last200)) score += 4;
    if (re.test(keywords)) score += 2;
    if (re.test(desc)) score += 1;
    if (re.test(path)) score += 0.5;
  }

  return score;
}


// ============================================================
//  SEARCH ENGINE — VERSION PONDÉRÉE
// ============================================================
function performSearch(q) {
  const query = q.trim().toLowerCase();

  if (!query) {
    return window.indexData
      .slice()
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  const terms = expandQuery(query);

  return window.indexData
    .map(it => {
      const hay = (
        (it.title || "") + " " +
        (it.description || "") + " " +
        (it.numero || "") + " " +
        (it.path || "") + " " +
        (it.keywords || "").toString()
      ).toLowerCase();

      const matches = terms.some(t =>
        hay.includes(t) ||
        hay.split(/[^a-z0-9à-öø-ÿ]+/).includes(t)
      );

      if (!matches) return null;

      return {
        ...it,
        _score: scoreDocument(it, terms)
      };
    })
    .filter(Boolean)
    .sort((a, b) => {
      if (b._score !== a._score) return b._score - a._score;
      return (b._dateObj || 0) - (a._dateObj || 0);
    });
}


// ============================================================
//  HIGHLIGHT LIMITÉ (max 3 occurrences)
// ============================================================
function highlight(text, terms) {
  if (!text) return "";

  let remaining = 3;
  let out = text;

  for (const t of terms) {
    if (remaining <= 0) break;

    const re = new RegExp(`\\b(${t})\\b`, "gi");

    out = out.replace(re, match => {
      if (remaining <= 0) return match;
      remaining--;
      return `<mark>${match}</mark>`;
    });
  }

  return out;
}


// ============================================================
//  RENDER RESULTS — TITRE CLIQUABLE + HIGHLIGHT
// ============================================================
function renderResults(list) {
  const container = document.getElementById("results");
  if (!container) return;

  let html = `
    <div class="info-tri" style="font-size:14px; margin-bottom:10px;">
      Résultats classés par pertinence (score + date)
    </div>
  `;

  const input =
    document.getElementById("search") ||
    document.getElementById("searchInput");
  const terms = expandQuery(input ? input.value : "");

  for (const it of list) {
    const date = it._dateObj ? it._dateObj.getFullYear() : "";
    const rawDesc = shorten(it.description || "");
    const desc = highlight(escapeHtml(rawDesc), terms);
    const titre = (it.numero && it.numero.trim()) ? it.numero : it.title;

    html += `
      <div class="result" style="margin-bottom:18px;">
        <div class="title-line" style="font-size:18px; font-weight:bold;">
          <a href="${escapeHtml(it._url)}" target="_blank"
             style="color:#0044cc; font-weight:bold; text-decoration:none;">
            ${escapeHtml(titre)}
          </a>
          <span class="date" style="margin-left:8px; color:#666; font-weight:normal;">
            ${escapeHtml(date)}
          </span>
        </div>

        <div class="filename" style="font-size:13px; color:#777; margin-top:2px;">
          ${escapeHtml(it.path)}
        </div>

        <div class="desc" style="font-size:14px; color:#333; margin-top:4px;">
          ${desc}
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}


// ------------------------------
// SHORT DESCRIPTION
// ------------------------------
function shorten(text) {
  if (!text) return "";
  text = String(text).replace(/\s+/g, " ").trim();
  if (text.length > 250) return text.substring(0, 250).trim() + "…";
  return text;
}


// ------------------------------
// UPDATE RESULTS
// ------------------------------
function updateResults() {
  const input =
    document.getElementById("search") ||
    document.getElementById("searchInput");

  const q = input ? input.value : "";
  results = performSearch(q);
  renderResults(results);
}


// ------------------------------
// INIT
// ------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadIndex();
    await loadGlossaire();
  } catch (e) {
    console.error("Erreur de chargement", e);
    const container = document.getElementById("results");
    if (container) container.innerHTML = "<div class='error'>Erreur de chargement.</div>";
    return;
  }

  const input =
    document.getElementById("search") ||
    document.getElementById("searchInput");

  if (input) {
    input.addEventListener("input", updateResults);
  }

  results = performSearch("");
  renderResults(results);
});
