// search.js — remplace entièrement ce fichier par ce bloc

// petite utilitaire pour résoudre un chemin relatif en URL absolue
function safeResolveUrl(path) {
  try {
    if (!path) return '';
    // si path est déjà absolu, URL le gère
    return new URL(path, location.origin).href;
  } catch (e) {
    return '';
  }
}

window._searchIndex = window._searchIndex || [];

async function loadIndex(){
  try{
    const resp = await fetch('/transport/index.json');
    if(!resp.ok) throw new Error('HTTP ' + resp.status);

    const text = await resp.text();
    const idx = JSON.parse(text);

    idx.forEach(item => {
      try {
        item._resolvedUrl = safeResolveUrl(item.path || '');
      } catch(e) {
        item._resolvedUrl = null;
      }
    });

    window._searchIndex = idx;
    console.log('index loaded, items:', idx.length);
    return idx;
  } catch(err) {
    console.error('Erreur lors du chargement de l index :', err && err.message ? err.message : err);
    window._searchIndex = [];
    return [];
  }
}

// Démarrage : charger l'index au chargement du script
// (on n'utilise pas de return au niveau global)
loadIndex().then(() => {
  console.log('search.js initialisé');
}).catch(e => {
  console.error('Erreur init search.js', e);
});
