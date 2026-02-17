// search.js — chargement index.json et recherche simple (adapté au nouveau HTML/CSS)
(function () {
  'use strict';

  const INDEX_URL = '/transport/index.json';
  const PAGE_SIZE = 12;

  const el = {
    q: document.getElementById('q'),
    btn: document.getElementById('search-btn'),
    results: document.getElementById('results'),
    info: document.getElementById('results-info'),
    prev: document.getElementById('prev'),
    next: document.getElementById('next'),
    pager: document.getElementById('pager'),
    pageInfo: document.getElementById('page-info')
  };

  let index = [];
  let filtered = [];
  let page = 1;

  function safeResolveUrl(path) {
    try { return new URL(path, location.origin).href; } catch (e) { return path || ''; }
  }

  async function loadIndex() {
    try {
      const r = await fetch(INDEX_URL, {cache: 'no-store'});
      if (!r.ok) throw new Error('HTTP ' + r.status);
      index = await r.json();
      index.forEach(i => i._resolvedUrl = safeResolveUrl(i.path || ''));
      console.log('index loaded, items:', index.length);
    } catch (e) {
      console.error('Erreur chargement index:', e && e.message ? e.message : e);
      index = [];
    }
  }

  function renderResults() {
    el.results.innerHTML = '';
    if (!filtered || filtered.length === 0) {
      el.info.textContent = 'Aucun résultat';
      el.pager.hidden = true;
      return;
    }
    const start = (page - 1) * PAGE_SIZE;
    const pageItems = filtered.slice(start, start + PAGE_SIZE);
    pageItems.forEach(item => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = item._resolvedUrl || item.path || '#';
      a.textContent = item.title || item.path || 'Sans titre';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      li.appendChild(a);

      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = item.type ? item.type : '';
      li.appendChild(meta);

      el.results.appendChild(li);
    });
    el.info.textContent = `Affichage ${start + 1}–${Math.min(start + PAGE_SIZE, filtered.length)} sur ${filtered.length}`;
    el.pageInfo.textContent = `Page ${page} / ${Math.ceil(filtered.length / PAGE_SIZE)}`;
    el.pager.hidden = filtered.length <= PAGE_SIZE;
  }

  function doSearch(term) {
    const t = (term || '').trim().toLowerCase();
    if (!t) {
      filtered = index.slice();
    } else {
      filtered = index.filter(it => {
        return (it.title && it.title.toLowerCase().includes(t))
          || (it.path && it.path.toLowerCase().includes(t))
          || (it.type && it.type.toLowerCase().includes(t));
      });
    }
    page = 1;
    renderResults();
  }

  el.btn.addEventListener('click', () => doSearch(el.q.value));
  el.q.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); doSearch(el.q.value); }
  });

  el.prev.addEventListener('click', () => { if (page > 1) { page--; renderResults(); } });
  el.next.addEventListener('click', () => { if (page * PAGE_SIZE < filtered.length) { page++; renderResults(); } });

  // initialisation
  loadIndex().then(() => {
    filtered = index.slice();
    renderResults();
  });

})();
