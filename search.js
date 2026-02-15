function normalize(str) {
    return str
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

function runSearch(query) {
    const qNorm = normalize(query || "");
    const container = document.getElementById("results");
    container.innerHTML = "";

    if (!qNorm) {
        container.innerHTML = "<p>Entrez un mot ou une expression ci-dessus.</p>";
        return;
    }

    fetch("search/index.json")
        .then(r => r.json())
        .then(data => {
            let count = 0;

            data.forEach(doc => {
                const textNorm = normalize(doc.content || "");
                const titleNorm = normalize(doc.title || "");

                if (textNorm.includes(qNorm) || titleNorm.includes(qNorm)) {
                    count++;
                    container.innerHTML += `
                        <div class="result">
                            <div class="result-title">
                                <a href="${doc.url}" target="_blank">${doc.title}</a>
                            </div>
                            <div class="result-year">
                                ${doc.year ? "Année : " + doc.year : ""}
                            </div>
                        </div>
                    `;
                }
            });

            if (count === 0) {
                container.innerHTML = "<p>Aucun document ne contient cette expression.</p>";
            }
        });
}

const params = new URLSearchParams(window.location.search);
const initialQuery = params.get("q") || "";
document.getElementById("searchBox").value = initialQuery;
runSearch(initialQuery);

document.getElementById("searchButton").onclick = function() {
    const q = document.getElementById("searchBox").value;
    runSearch(q);
};
document.get
