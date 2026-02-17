// -----------------------------
// Helpers à placer en tête
// -----------------------------
window.normalizeForSearch = function(s){
  return (s||'').toString().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
};

const baseForIndex = (() => {
  try {
    return location.origin + location.pathname.replace(/\/[^/]*$/, '/');
  } catch(e) {
    return window.location.href.replace(/\/[^/]*$/, '/');
  }
})();

function safeResolveUrl(path){
  if(!path) return null;
  try{
    return new URL(path, baseForIndex).toString();
  }catch(e){
    try{
      const parts = path.split('/').map(p => {
        try { return encodeURIComponent(decodeURIComponent(p)).replace(/%2F/g, '/'); }
        catch(_) { return encodeURIComponent(p).replace(/%2F/g, '/'); }
      });
      return new URL(parts.join('/'), baseForIndex).toString();
    }catch(e2){
      return baseForIndex + encodeURI(path);
    }
  }
}

// -----------------------------
// Chargement sécurisé de l'index
// -----------------------------
async function loadIndex(){
  try{
    const resp = await fetch('index.json');
    if(!resp.ok) throw new Error('HTTP ' + resp.status);

    // DEBUG: afficher headers utiles
    console.log('loadIndex: content-type=', resp.headers.get('content-type'));
    console.log('loadIndex: content-length=', resp.headers.get('content-length'));

    const text = await resp.text();

    // DEBUG: montrer début/fin et longueur pour repérer BOM/HTML/troncature
    console.log('loadIndex: text length=', text.length);
    console.log('loadIndex: start=', JSON.stringify(text.slice(0,120)));
    console.log('loadIndex: end=', JSON.stringify(text.slice(-120)));

    // Essayer de parser et, en cas d'erreur, loguer un extrait utile
    let idx;
    try {
      idx = JSON.parse(text);
    } catch(parseErr) {
      console.error('loadIndex: JSON.parse failed:', parseErr && parseErr.message ? parseErr.message : parseErr);
      // afficher un extrait plus large autour de la fin pour "Expected ']'"
      console.error('loadIndex: problematic tail (500 chars):', text.slice(-500));
      window._searchIndex = [];
      return [];
    }

    idx.forEach(item => {
      try { item._resolvedUrl = safeResolveUrl(item.url || ''); }
      catch(e){ item._resolvedUrl = null; }
    });
    window._searchIndex = idx;
    console.log('index loaded, items:', idx.length);
    return idx;
  }catch(err){
    console.error('Erreur lors du chargement de l index :', err && err.message ? err.message : err);
    window._searchIndex = [];
    return [];
  }
}


// -----------------------------
// Fonctions de recherche exposées
// -----------------------------
window.searchIndex = function(query, index){
  if(!query || !index || !Array.isArray(index)) return [];
  const q = window.normalizeForSearch(query.trim());
  if(!q) return [];
  return index.filter(item => {
    const title = window.normalizeForSearch(item.title || "");
    const content = window.normalizeForSearch(item.content || "");
    const url = window.normalizeForSearch(item.url || "");
    const year = window.normalizeForSearch(item.year || "");
    return title.includes(q) || content.includes(q) || url.includes(q) || year.includes(q);
  });
};

window.performSearch = function(query){
  const idx = window._searchIndex || [];
  const results = window.searchIndex(query, idx);
  if(typeof window.displayResults === 'function'){
    window.displayResults(results);
  } else {
    // fallback d'affichage
    const out = document.getElementById('results') || document.body;
    if(results.length === 0){
      out.innerHTML = '<p>Aucun résultat trouvé.</p>';
    } else {
      out.innerHTML = '';
      results.forEach(item => {
        const div = document.createElement('div');
        div.className = 'result';
        const url = item._resolvedUrl || item.url || '#';
        div.innerHTML = `
          <div class="result-title">${item.title || '—'}</div>
          <div class="result-year">${item.year || '—'}</div>
          <a href="${url}" target="_blank" rel="noopener noreferrer">📄 Ouvrir le document</a>
        `;
        out.appendChild(div);
      });
    }
  }
};

// -----------------------------
// Si tu as déjà une displayResults, garde-la ; sinon la fallback ci-dessus suffit.
// -----------------------------
function displayResults(results) {
  // Si tu veux forcer l'utilisation de la fonction globale, décommente la ligne suivante :
  // return window.performSearch === displayResults ? null : window.performSearch;
  // (ici on laisse la fallback gérée dans performSearch)
}

// -----------------------------
// Initialisation DOM et interception du formulaire
// -----------------------------
document.addEventListener('DOMContentLoaded', async () => {
  // Charge l'index (attend la fin pour garantir disponibilité)
  const index = await loadIndex();

  // Sélecteurs : adapte si tes IDs diffèrent
  const input = document.getElementById('searchBox') || document.querySelector('input[name="q"]');
  const button = document.getElementById('searchButton') || document.querySelector('button[type="submit"]');
  const form = document.querySelector('form#searchForm') || document.querySelector('form');

  // Intercepter la soumission du formulaire pour éviter la navigation
  if(form){
    form.addEventListener('submit', e => {
      e.preventDefault();
      const q = input ? input.value : '';
      window.performSearch(q);
    });
  }

  // Clic sur le bouton
  if(button){
    button.addEventListener('click', e => {
      e.preventDefault();
      const q = input ? input.value : '';
      window.performSearch(q);
    });
  }

  // Entrée clavier dans le champ
  if(input){
    input.addEventListener('keydown', e => {
      if(e.key === 'Enter'){
        e.preventDefault();
        window.performSearch(input.value);
      }
    });
  }

  // Expose un raccourci console pour tests rapides
  window.performSearchConsole = function(q){
    const res = window.searchIndex(q, window._searchIndex || []);
    console.log('performSearchConsole results', res.length, res.slice(0,10));
    return res;
  };

  console.log('search.js initialisé');
});
