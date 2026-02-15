let idx = null;
let documents = [];

// Charger l'index JSON
fetch("index.json")
  .then(response => response.json())
  .then(data => {
    documents = data;

    idx = lunr(function () {
      this.ref("url");
      this.field("title");
      this.field("content");

      documents.forEach(doc => this.add(doc));
    });
  })
  .catch(err => {
    console.error("Erreur chargement index.json :", err);
  });

// Fonction appelée à chaque frappe dans la barre de recherche
function runSearch() {
  const query = document.getElementById("search-box").value.trim();

  if (!idx || query.length < 2) {
    document.getElementById("results").innerHTML = "";
    return;
  }

  let results;
  try {
    results = idx.search(query);
  } catch (e) {
    console.error("Erreur Lunr :", e);
    return;
  }

  const html = results.map(result => {
    const doc = documents.find(d => d.url === result.ref);

    if (!doc) return "";

    // Surlignage simple
    const highlight = (text) =>
      text.replace(new RegExp(query, "gi"), match => `<mark>${match}</mark>`);

    return `
      <div class="item">
        <a href="/transport/${doc.url}" target="_blank">${highlight(doc.title)}</a>
        <p>${highlight(doc.content)}</p>
      </div>
    `;
  }).join("");

  document.getElementById("results").innerHTML = html;
}

