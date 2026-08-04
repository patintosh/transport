import pandas as pd
import plotly.graph_objects as go

# 1. Chargement du fichier global généré par le scraper
df = pd.read_csv("historique_global.csv")

# Nettoyage et conversion des dates pour le tri chronologique
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
df = df.sort_values("date")
df["Date Vol Str"] = df["date"].dt.strftime("%d/%m/%Y")

# Création d'une colonne liaison normalisée (ex: AJA-ORY)
df["Liaison"] = df["origin"] + "-" + df["destination"]

# 2. Identification des aéroports uniques
aeroports = sorted(list(set(df["origin"].unique()).union(set(df["destination"].unique()))))

# 3. Création de la figure Plotly
fig = go.Figure()
trace_counter = 0

for aeroport in aeroports:
    df_aeroport = df[(df["origin"] == aeroport) | (df["destination"] == aeroport)]
    liaisons = sorted(df_aeroport["Liaison"].unique())
    
    for liaison in liaisons:
        df_liaison = df_aeroport[df_aeroport["Liaison"] == liaison]
        
        fig.add_trace(
            go.Scatter(
                x=df_liaison["Date Vol Str"],
                y=df_liaison["avg"],
                mode="lines+markers",
                name=f"Liaison {liaison}",
                visible=False
            )
        )
        trace_counter += 1

current_trace_idx = 0
dropdown_buttons = []

for idx, aeroport in enumerate(aeroports):
    df_aeroport = df[(df["origin"] == aeroport) | (df["destination"] == aeroport)]
    liaisons_count = df_aeroport["Liaison"].nunique()
    
    visibility = [False] * trace_counter
    for i in range(current_trace_idx, current_trace_idx + liaisons_count):
        visibility[i] = True
        
    if idx == 0:
        for i in range(current_trace_idx, current_trace_idx + liaisons_count):
            fig.data[i].visible = True

    dropdown_buttons.append(
        {
            "args": [{"visible": visibility}],
            "label": f"Aéroport : {aeroport}",
            "method": "update"
        }
    )
    current_trace_idx += liaisons_count

# 4. Mise en page du graphique
fig.update_layout(
    updatemenus=[
        {
            "buttons": dropdown_buttons,
            "direction": "down",
            "showactive": True,
            "x": 0.17,
            "xanchor": "left",
            "y": 1.15,
            "yanchor": "top"
        }
    ],
    title={
        "text": "Suivi des prix moyens des liaisons par aéroport",
        "y": 0.95,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top"
    },
    xaxis_title="Date",
    yaxis_title="Prix Moyen (€)",
    template="plotly_white",
    hovermode="x unified"
)

# 5. Exportation en HTML
fig.write_html("dashboard.html", include_plotlyjs="cdn")
print("Dashboard généré avec succès à partir de l'historique global !")