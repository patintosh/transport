import pandas as pd
import plotly.graph_objects as go
import glob
import os

CSS = """
<style>
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 40px;
  background: #0f172a;
  color: #e5e7eb;
}
h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}
h2 {
  margin-top: 2rem;
  margin-bottom: 0.5rem;
}
a {
  color: #38bdf8;
}
.table-container {
  margin-top: 2rem;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin-top: 0.5rem;
}
th, td {
  border: 1px solid #1f2937;
  padding: 6px 10px;
  text-align: right;
}
th {
  background: #111827;
}
tr:nth-child(even) {
  background: #020617;
}
tr:nth-child(odd) {
  background: #030712;
}
.route-name {
  text-align: left;
}
</style>
"""

def generate_dashboard():
    html_parts = []
    html_parts.append("<html><head>")
    html_parts.append(CSS)
    html_parts.append("</head><body>")
    html_parts.append("<h1>Air Corsica – Monitoring des prix</h1>")

    # Tableau des prix moyens par route (global)
    summary_rows = []

    for file in glob.glob("routes_aircorsica/*.csv"):
        df = pd.read_csv(file)
        route = os.path.basename(file).replace(".csv", "")
        origin, dest = route.split("_")

        html_parts.append(f"<h2>{origin} → {dest}</h2>")

        # Courbes min / max / mean
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["scrape_date"],
            y=df["mean"],
            mode="lines+markers",
            name="Prix moyen",
            line=dict(color="#38bdf8")
        ))
        fig.add_trace(go.Scatter(
            x=df["scrape_date"],
            y=df["min"],
            mode="lines+markers",
            name="Min",
            line=dict(color="#22c55e")
        ))
        fig.add_trace(go.Scatter(
            x=df["scrape_date"],
            y=df["max"],
            mode="lines+markers",
            name="Max",
            line=dict(color="#ef4444")
        ))

        fig.update_layout(
            title=f"Évolution des prix – {origin} → {dest}",
            xaxis_title="Date de scraping",
            yaxis_title="Prix (€)",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#020617",
            font=dict(color="#e5e7eb")
        )

        graph_html = fig.to_html(full_html=False)
        html_parts.append(graph_html)

        # Lien de téléchargement
        html_parts.append(f"<p><a href='{file}'>Télécharger la série CSV</a></p>")

        # Ligne de résumé pour le tableau global
        summary_rows.append({
            "route": f"{origin} → {dest}",
            "mean_mean": df["mean"].mean(),
            "mean_min": df["min"].mean(),
            "mean_max": df["max"].mean()
        })

    # Tableau global des moyennes
    if summary_rows:
        html_parts.append("<div class='table-container'>")
        html_parts.append("<h2>Résumé des prix moyens par liaison</h2>")
        html_parts.append("<table>")
        html_parts.append("<tr><th class='route-name'>Liaison</th><th>Prix moyen</th><th>Min moyen</th><th>Max moyen</th></tr>")
        for row in summary_rows:
            html_parts.append(
                f"<tr>"
                f"<td class='route-name'>{row['route']}</td>"
                f"<td>{row['mean_mean']:.2f}</td>"
                f"<td>{row['mean_min']:.2f}</td>"
                f"<td>{row['mean_max']:.2f}</td>"
                f"</tr>"
            )
        html_parts.append("</table>")
        html_parts.append("</div>")

    html_parts.append("</body></html>")

    os.makedirs("docs", exist_ok=True)
    with open("docs/air_corsica.html", "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

if __name__ == "__main__":
    generate_dashboard()
