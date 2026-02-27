// ============================================================
//  SEARCH ENGINE — VERSION PROPRE ET STABLE
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
//  DATE EXTRACTION — VERSION SÉCURISÉE
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
let SORT_MODE = "recent";



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
//  LOAD GLOSSAIRE
// ============================================================
async function loadGlossaire() {
  try {
    const resp = await fetch("glossaireinverse.json", { cache: "no-store" });
    if (resp.ok) GLOSSAIRE = await resp.json();
  } catch (e) {
    console.warn("Glossaire non chargé");
  }
}



// ============================================================
//  EXPANSION MULTI-TERMES — VERSION STABLE
// ============================================================
function expandQuery(q) {
  const base = q.trim().toLowerCase();
  if (!base) return [];

  const terms = new Set();

  // 1) Expression complète
  terms.add(base);

  // 2) Synonymes expression complète
  if (GLOSSAIRE[base]) {
    for (const syn of GLOSSAIRE[base]) {
      terms.add(String(syn).toLowerCase());
    }
  }

  // 3) Découpage en mots simples
  let words = base.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);
  words = words.filter(w => w.length >= 3);

  for (const w of words) {
    terms.add(w);

    if (GLOSSAIRE[w]) {
      for (const syn of GLOSSAIRE[w]) {
        terms.add(String(syn).toLowerCase());
      }
    }

    if (w.endsWith("s")) terms.add(w.slice(0, -1));
    else terms.add(w + "s");
  }

  // 4) Expansion multi-mots (si pas dans le glossaire)
  const expanded = Array.from(terms);
  for (const t of expanded) {
    if (!t.includes(" ")) continue;
    if (GLOSSAIRE[t]) continue;

    let parts = t.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);
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

  // 5) Si un multi-mot est présent, retirer ses composants simples
  const final = new Set(terms);
  for (const t of terms) {
    if (t.includes(" ")) {
      const parts = t.split(/[^a-z0-9à-öø-ÿ]+/).filter(Boolean);
      for (const p of parts) {
        if (p.length >= 3) final.delete(p);
      }
    }
  }

  return Array.from(final);
}



// ============================================================
//  SCORE DOCUMENT — VERSION MULTI-MOTS
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

    // Multi-mots : match simple
    if (t.includes(" ")) {
      if (title.includes(t)) score += 6;
      if (first200.includes(t)) score += 4;
      if (last200.includes(t)) score += 3;
      if (keywords.includes(t)) score += 1;
      if (desc.includes(t)) score += 1;
      if (path.includes(t)) score += 0.5;
      continue;
    }

    // Mots simples : regex stricte
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
//  SEARCH ENGINE — MATCH + SCORE + TRI
// ============================================================
function performSearch(q) {
  const query = q.trim().toLowerCase();

  if (!query) {
    return window.indexData
      .slice()
      .sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));
  }

  const terms = expandQuery(query);

  const scored = window.indexData
    .map(it => {
      const hay = (
        (it.title || "") + " " +
        (it.description || "") + " " +
        (it.numero || "") + " " +
        (it.path || "") + " " +
        (it.keywords || "").toString()
      ).toLowerCase();

      // Matching strict par mots
      const tokens = hay.split(/[^a-z0-9à-öø-ÿ]+/);

      const matches = terms.some(t => {
        if (t.includes(" ")) {
          // Multi-mots : match robuste
          const pattern = t.replace(/\s+/g, "\\s+");
          const re = new RegExp(pattern, "i");
          return re.test(hay);
        }

        // Mots simples
        return tokens.includes(t);
      });

      if (!matches) return null;

      const baseScore = scoreDocument(it, terms);

      return {
        ...it,
        _textScore: Math.sqrt(baseScore)
      };
    })
    .filter(Boolean);

  // Tri date
  scored.sort((a, b) => (b._dateObj || 0) - (a._dateObj || 0));

  // Tri pertinence dans années proches
  return scored.sort((a, b) => {
    const da = a._dateObj ? a._dateObj.getFullYear() : 0;
    const db = b._dateObj ? b._dateObj.getFullYear() : 0;

    if (da === db) return b._textScore - a._textScore;
    if (Math.abs(da - db) <= 1)
      return (db - da) * 0.7 + (b._textScore - a._textScore) * 0.3;

    return db - da;
  });
}



// ============================================================
//  TRI FINAL SELON LE TOGGLE
// ============================================================
function applyDateSort(list) {
  return list.slice().sort((a, b) => {
    const da = a._dateObj;
    const db = b._dateObj;

    if (!da && !db) return 0;
    if (!da) return 1;
    if (!db) return -1;

    return SORT_MODE === "recent" ? db - da : da - db;
  });
}



// ============================================================
//  RENDER RESULTS
// ============================================================
function renderResults(list) {
  const container = document.getElementById("results");
  if (!container) return;

  let html = `
    <div class="info-tri" style="font-size:14px; margin-bottom:10px;">
      Tri : ${SORT_MODE === "recent" ? "récents → anciens" : "anciens → récents"}
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



// ============================================================
//  HIGHLIGHT LIMITÉ
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



// ------------------------------
// SHORT DESCRIPTION
// ------------------------------
function shorten(text) {
  if (!text) return "";
  text = String(text).replace(/\s+/g, " ").trim();
  if (text.length > 250) return text.substring(0, 250).trim() + "…";
  return text;
}



// ============================================================
//  UPDATE RESULTS
// ============================================================
function updateResults() {
  const input =
    document.getElementById("search") ||
    document.getElementById("searchInput");

  const q = input ? input.value : "";
  results = performSearch(q);
  results = applyDateSort(results);
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

  const toggle = document.getElementById("toggleTri");
  if (toggle) {
    toggle.addEventListener("click", () => {
      SORT_MODE = SORT_MODE === "recent" ? "ancien" : "recent";
      toggle.textContent =
        SORT_MODE === "recent"
          ? "Trier : récents → anciens"
          : "Trier : anciens → récents";
      updateResults();
    });
  }

  results = performSearch("");
  results = applyDateSort(results);
  renderResults(results);
});
