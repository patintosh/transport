// ============================================================
//  SEARCH ENGINE — VERSION AMÉLIORÉE (Chapitres 1–3)
//  Date : 24 février 2026 — PARTIE 1 / 3
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


// ============================================================
//  DATE EXTRACTION — VERSION SÉCURISÉE (Chapitre 3)
// ============================================================
function extractDate(it) {
  if (!it.date) return null;

  const raw = String(it.date).trim().toLowerCase();

  // 1) Format JJ.MM.AAAA / JJ-MM-AAAA / JJ/MM/AAAA
  let m = raw.match(/(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})/);
  if (m) {
    let d = Math.min(Number(m[1]), 28);
    let mo = Math.min(Number(m[2]), 12);
    let y = Number(m[3]);
    return new Date(y, mo - 1, d);
  }

  // 2) Format JJ mois AAAA
  m = raw.match(/(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})/);
  if (m) {
    const mois = {
      janvier:0, février:1, mars:2, avril:3, mai:4, juin:5,
      juillet:6, août:7, septembre:8, octobre:9, novembre:10, décembre:11
    };
    let d = Math.min(Number(m[1]), 28);
    let mo = mois[m[2]];
    let y = Number(m[3]);
    return new Date(y, mo, d);
  }

  // 3) Format mois AAAA
  m = raw.match(/(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})/);
  if (m) {
    const mois = {
      janvier:0, février:1, mars:2, avril:3, mai:4, juin:5,
      juillet:6, août:7, septembre:8, octobre:9, novembre:10, décembre:11
    };
    let mo = mois[m[1]];
    let y = Number(m[2]);
    return new Date(y, mo, 1);
  }

  // 4) Format AAAA
  m = raw.match(/(19|20)\d{2}/);
  if (m) {
    return new Date(Number(m[0]), 0, 1);
  }

  return null;
}



// ------------------------------
// GLOBALS
// ------------------------------
window.indexData = [];
let GLOSSAIRE = {};
let results = [];


// ============================================================
//  LOAD INDEX.JSON
// ============================================================
async function loadIndex() {
  const resp = await fetch("index.json", { cache: "no-store" });
  if (!resp.ok) throw new Error("index.json introuvable");

  window.indexData = await resp.json();

  for (const it of window.indexData) {
    it._url = normalizePath(it.path);
    it._dateObj = extractDate(it);
  }
}


// ============================================================
//  LOAD GLOSSAIRE (depuis glossaire_fusionne.json)
// ============================================================
async function loadGlossaire() {
  try {
    const resp = await fetch("glossaire_fusionne.json", { cache: "no-store" });
    if (resp.ok) GLOSSAIRE = await resp.json();
  } catch (e) {
    console.warn("Glossaire non chargé");
  }
}


// ============================================================
//  EXPANSION MULTI-TERMES — VERSION GLOSSAIRE RENFORCÉE
// ============================================================
function expandQuery(q) {
  const base = q.trim().toLowerCase();
  if (!base) return [];

  const terms = new Set();

  // 1) Expression complète
  terms.add(base);

  // 2) Synonymes de l'expression complète (multi-mots inclus)
  if (GLOSSAIRE[base]) {
    for (const syn of GLOSSAIRE[base]) {
      terms.add(String(syn).toLowerCase());
    }
  }

  // 3) Découpage en mots simples
  let words = base.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);

  // Stopwords : on ignore les mots trop courts (< 3 lettres)
  words = words.filter(w => w.length >= 3);

  for (const w of words) {
    terms.add(w);

    // Synonymes du mot simple
    if (GLOSSAIRE[w]) {
      for (const syn of GLOSSAIRE[w]) {
        terms.add(String(syn).toLowerCase());
      }
    }

    // Variantes singulier/pluriel
    if (w.endsWith("s")) {
      terms.add(w.slice(0, -1));
    } else {
      terms.add(w + "s");
    }
  }

  // 4) Expansion multi-mots : si un terme contient plusieurs mots,
  //    on ajoute aussi chaque mot individuellement et leurs synonymes.
  const expanded = Array.from(terms);
  for (const t of expanded) {
    if (t.includes(" ")) {
      let parts = t.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);

      // Stopwords ici aussi
      parts = parts.filter(p => p.length >= 3);

      for (const p of parts) {
        terms.add(p);

        if (GLOSSAIRE[p]) {
          for (const syn of GLOSSAIRE[p]) {
            terms.add(String(syn).toLowerCase());
          }
        }
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

    if (re.test(title)) score += 6;
if (re.test(first200)) score += 4;
if (re.test(last200)) score += 3;
if (re.test(keywords)) score += 1;
if (re.test(desc)) score += 1;
if (re.test(path)) score += 0.5;

  }

  return score;
}


// ============================================================
//  BONUS DATE — SURPONDÉRATION
// ============================================================
function dateBonus(it) {
  if (!it._dateObj) return 0;

  const year = it._dateObj.getFullYear();
  if (year < 1950 || year > 2025) return 0;

  return ((year - 1950) / 100) * 6;
}


// ============================================================
//  SEARCH ENGINE — VERSION PONDÉRÉE (score + date)
// ============================================================
function performSearch(q) {
  const query = q.trim().toLowerCase();

  // Cas : champ vide → tri chrono simple
  if (!query) {
    return window.indexData
      .slice()
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  const terms = expandQuery(query);

  // 1) On calcule le score textuel
  const scored = window.indexData
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

      const baseScore = scoreDocument(it, terms);
      return {
        ...it,
        _textScore: Math.sqrt(baseScore)
      };
    })
    .filter(Boolean);

  // 2) On trie par date d'abord
  scored.sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));

  // 3) Puis on trie par score textuel *à l'intérieur des années proches*
  const FINAL = scored.sort((a, b) => {
    const da = a._dateObj ? a._dateObj.getFullYear() : 0;
    const db = b._dateObj ? b._dateObj.getFullYear() : 0;

    // même année → tri par pertinence
    if (da === db) return b._textScore - a._textScore;

    // années proches (±1 an) → pertinence joue un peu
    if (Math.abs(da - db) <= 1) {
      return (db - da) * 0.7 + (b._textScore - a._textScore) * 0.3;
    }

    // années éloignées → la date domine
    return db - da;
  });

  return FINAL;
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
//  RENDER RESULTS — TITRE CLIQUABLE + HIGHLIGHT + DATE
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


// ============================================================
//  INIT
// ============================================================
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
