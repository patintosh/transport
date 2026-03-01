let DATA = [];
let SORT_MODE = "recent";

function normalizePath(path) {
    if (!path) return "#";
    if (path.startsWith('http')) return path;
    let p = path.trim().replace(/^\//, '');
    return window.location.hostname.includes('github.io') ? '/transport/' + p : p;
}

function extraireAnnee(it) {
    const m = String(it.date || "").match(/(\d{4})/);
    return m ? m[1] : "0000";
}

async function init() {
    const resp = await fetch("index.json");
    DATA = await resp.json();
    document.getElementById("search-input").addEventListener("input", update);
    document.getElementById("toggleSortDate").addEventListener("click", () => {
        SORT_MODE = (SORT_MODE === "recent") ? "old" : "recent";
        document.getElementById("toggleSortDate").textContent = SORT_MODE === "recent" ? "📅 Plus récents" : "📅 Plus anciens";
        update();
    });
}

function update() {
    const q = document.getElementById("search-input").value.toLowerCase();
    const res = DATA.filter(it => (it.title + " " + (it.description || "")).toLowerCase().includes(q));
    
    res.sort((a, b) => {
        const dA = extraireAnnee(a), dB = extraireAnnee(b);
        return SORT_MODE === "recent" ? dB.localeCompare(dA) : dA.localeCompare(dB);
    });

    render(res);
}

function render(arr) {
    const pdfDiv = document.getElementById("results-pdf");
    const simDiv = document.getElementById("results-simdif");
    pdfDiv.innerHTML = ""; simDiv.innerHTML = "";
    document.getElementById("result-count").innerText = `${arr.length} résultats`;

    arr.forEach(it => {
        const isPDF = it.path.toLowerCase().endsWith('.pdf');
        const html = `
            <div class="result-item">
                <a href="${normalizePath(it.path)}" target="_blank">${it.title}</a>
                <p style="font-size:0.9rem; color:#444; margin:8px 0;">${it.description || ""}</p>
                <div style="font-size:0.8rem; color:#888;">📅 ${it.date || "Date inconnue"}</div>
            </div>`;
        if (isPDF) pdfDiv.innerHTML += html; else simDiv.innerHTML += html;
    });
}

window.onload = init;