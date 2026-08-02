import os
import pandas as pd
import plotly.express as px

# 1. Chargement des données (version standard avec point)
df_series = pd.read_csv("series_vols_aircorsica.csv")

# Nettoyage / Préparation des liaisons (ex: AJA-ORY, NCE-BIA, etc.)
# On extrait l'aéroport du continent et l'aéroport corse
df_series["Continent"] = df_series["Liaison"].apply(
    lambda x: x.split("-")[0]
    if x.split("-")[0] in ["ORY", "CDG", "MRS", "NCE", "LYS", "TLS"]
    else x.split("-")[1]
)
df_series["Corse"] = df_series["Liaison"].apply(
    lambda x: x.split("-")[1]
    if x.split("-")[0] in ["ORY", "CDG", "MRS", "NCE", "LYS", "TLS"]
    else x.split("-")[0]
)

# 2. Création de la figure interactive groupée par aéroport du continent
fig = px.line(
    df_series,
    x="Date Vol",
    y="Moyenne Light (€)",
    color="Liaison",
    line_dash="Continent",
    markers=True,
    title="Suivi des Prix Moyens Air Corsica - Par Liaison et Aéroport",
    labels={
        "Moyenne Light (€": "Prix Moyen Light (€)",
        "Date Vol": "Date du Vol",
    },
)

fig.update_layout(
    template="plotly_white",
    xaxis_tickangle=-45,
    legend_title="Liaisons",
)

# 3. Export en page HTML autonome
dashboard_html = fig.to_html(full_html=True, include_plotlyjs="cdn")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print("Page HTML générée avec succès : index.html")
