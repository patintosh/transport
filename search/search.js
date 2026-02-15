let idx = null;
let documents = [];

async function loadIndex() {
  const response = await fetch('index.json');
  documents = await response.json();

  idx = lunr(function () {
    this.ref('id');
    this.field('title');
    this.field('content');

    documents.forEach((doc, i) => {
      doc.id = i;
      this.add(doc);
    });
  });
}

async function runSearch() {
  if (!idx) await loadIndex();

  const query = document.getElementById('search-box').value.trim();
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (query.length < 2) return;

  const results = idx.search(query);

  if (results.length === 0) {
    resultsDiv.innerHTML = "<p>Aucun résultat.</p>";
    return;
  }

  results.forEach(r => {
    const doc = documents[r.ref];
    const item = document.createElement('div');
    item.className = 'item';

    item.innerHTML = `
      <a href="${doc.url}">${doc.title}</a>
      <p>${doc.content.substring(0, 160)}...</p>
    `;

    resultsDiv.appendChild(item);
  });
}
