// Chargement du fichier index.json
async function loadIndex() {
  try {
    const response = await fetch('index.json');
    if (!response.ok) {
      throw new Error(`Erreur HTTP : ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Erreur lors du chargement de l'index :", error);
    return [];
  }
}

// Fonction de normalisation (accents, majuscules, etc.)
function normalize(text) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

// Fonction de recherche
function searchIndex(query, index) {
  const q = normalize(query);

  return index.filter(entry => {
    const title = normalize(entry.title || "");
    const content = normalize(entry.content || "");
    const year = normalize(entry.year || "");
    return (
      title.includes(q) ||
      content.includes(q) ||
      year.includes(q)
    );
  });
}

// Affichage des résultats
function displayResults(results) {
  const container = document.getElementById("results");
  container.innerHTML = "";

  if (results.length === 0) {
    container.innerHTML = "<p>Aucun résultat trouvé.</p>";
    return;
  }

  results.forEach(item => {
    const div = document.createElement("div");
    div.className = "result-item";

    div.innerHTML = `
      <h3>${item.title}</h3>
      <p><strong>Année :</strong> ${item.year || "—"}</p>
      <a href="${item.url}" target="_blank">📄 Ouvrir le document</a>
    `;

    container.appendChild(div);
  });
}

// Initialisation
document.addEventListener("DOMContentLoaded", async () => {
  const index = await loadIndex();

  const input = document.getElementById("searchInput");
  const form = document.getElementById("searchForm");

  form.addEventListener("submit", event => {
    event.preventDefault();
    const query = input.value.trim();
    const results = searchIndex(query, index);
    displayResults(results);
  });
});
