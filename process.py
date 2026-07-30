from datetime import datetime
import pandas as pd


def traiter_series_temporelles(chemin_fichier="vols_aircorsica.csv"):
  try:
    df = pd.read_csv(chemin_fichier)
  except FileNotFoundError:
    print(f"❌ Le fichier {chemin_fichier} est introuvable.")
    return

  # Extraction de la date de capture (sans l'heure) et conversion des dates
  df["Date_Capture_Seule"] = pd.to_datetime(
      df["Date de capture"]
  ).dt.strftime("%Y-%m-%d")
  df["dt_capture"] = pd.to_datetime(
      df["Date de capture"].astype(str).str.slice(0, 10), format="%Y-%m-%d"
  )
  df["dt_vol"] = pd.to_datetime(df["Date vol"], format="%d/%m/%Y")

  # Filtrage strict J+7
  df["J_cible"] = (df["dt_vol"] - df["dt_capture"]).dt.days
  df_j7 = df[df["J_cible"] == 7].copy()

  if df_j7.empty:
    print(
        "⚠️ Aucun vol ne correspond exactement à l'horizon J+7 dans le CSV"
        " actuel."
    )
    return

  # Nettoyage des prix
  df_j7["Prix_net"] = (
      df_j7["Prix"]
      .astype(str)
      .str.replace(r"[^0-9]", "", regex=True)
  )
  df_j7["Prix_net"] = pd.to_numeric(df_j7["Prix_net"], errors="coerce")
  df_j7 = df_j7.dropna(subset=["Prix_net"])

  # Agrégation quotidienne par liaison (Moyenne, Min, Max)
  indicateurs_quotidiens = (
      df_j7.groupby(["Date_Capture_Seule", "Arrivée"])
      .agg(
          Prix_Moyen=("Prix_net", "mean"),
          Prix_Mini=("Prix_net", "min"),
          Prix_Maxi=("Prix_net", "max"),
          Nombre_Vols_Trouves=("Prix_net", "count"),
      )
      .reset_index()
  )

  # Tri chronologique (du plus vieux au plus récent)
  indicateurs_quotidiens = indicateurs_quotidiens.sort_values(
      by=["Date_Capture_Seule", "Arrivée"]
  )
  indicateurs_quotidiens["Prix_Moyen"] = indicateurs_quotidiens[
      "Prix_Moyen"
  ].round(2)

  # Sauvegarde du fichier exploitable pour les séries chronologiques
  indicateurs_quotidiens.to_csv(
      "series_temporelles_j7.csv", index=exports := False, encoding="utf-8-sig"
  )
  print("✅ Séries chronologiques J+7 générées avec succès.")


if __name__ == "__main__":
  traiter_series_temporelles()
