      
let idx = null;
let documents = null;

async function loadIndex() {
  const response = await fetch('index.json');
  documents = await response.json();

  idx = lunr(function () {
    this.ref('url');
    this.field('title');
    this.field('content');

   
    documents.forEach(doc => this.add(doc));
  });
}

async function runSearch() {
  if (!idx) await loadIndex();

  const query = document.getElementById('search-box').value;
  const results = idx.search(query);

  const container = document.getElementById('results');
  container.innerHTML = '';

  if (results.length === 0) {
    container.innerHTML = '<p>Aucun résultat.</p>';
    return;
  }

  results.forEach(result => {
    const doc = documents.find(d => d.url === result.ref);
    const div = document.createElement('div');
    div.innerHTML = `<p><a href="${doc.url}">${doc.title}</a></p>`;
    container.appendChild(div);
  });
}
