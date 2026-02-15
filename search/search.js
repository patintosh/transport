function normalize(str) {
    return str
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

const params = new URLSearchParams(window.location.search);
const query = params.get("q") || "";
const qNorm = normalize(query);

fetch("search/index.json")
    .then(r => r.json())
    .then(data => {
        const container = document.getElementById("results");
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
