import re
import pandas as pd


def clean_price(val):
  """Nettoie la chaîne de prix pour la convertir en float et exclut

  l'artefact parasite de 51 €.
  """
  if pd.isna(val):
    return None
  s = (
      str(val)
      .replace("€", "")
      .replace("TTC", "")
      .replace("\xa0", "")
      .strip()
  )
  s = re.sub(r"[^\d,\.]", "", s)
  s = s.replace(",", ".")
  try:
    price = float(s)
    if price == 51.0:  # Exclusion de la valeur aberrante
      return None
    return price
  except ValueError:
    return None


def traiter_series_temporelles():
  input_file = "vols_aircorsica.csv"
  output_file = "series_temporelles_j7.csv"

  try:
    df = pd.read_csv(input_file)
  except FileNotFoundError:
    print(f"Erreur : Le fichier {input_file} est introuvable.")
    return

  if df.empty:
    print("Le fichier CSV est vide.")
    return

  # 1. Nettoyage de la colonne Prix
  if "Prix" in df.columns:
    df["Prix_Numeric"] = df["Prix"].apply(clean_price)
  else:
    print("Erreur : Colonne 'Prix' introuvable dans le CSV.")
    return

  # 2. Normalisation de la date de capture
  date_col = None
  for col in df.columns:
    if "date" in col.lower() or "capture" in col.lower():
      date_col = col
      break

  if date_col:
    df["Date_Capture_Seule"] = pd.to_datetime(
        df[date_col], format="mixed", errors="coerce"
    ).dt.date

  df = df.dropna(subset=["Date_Capture_Seule", "Prix_Numeric"])

  # 3. Définition des clés de regroupement pour l'agrégation par liaison et par jour
  group_cols = ["Date_Capture_Seule", "Départ", "Arrivée", "Date vol"]
  group_cols = [col for col in group_cols if col in df.columns]

  if not group_cols:
    print("Erreur : Colonnes d'agrégation introuvables.")
    return

  # 4. Calcul des indicateurs statistiques (Min, Moyen, Max, Nombre de vols)
  df_agg = (
      df.groupby(group_cols, dropna=False)["Prix_Numeric"]
      .agg(
          Prix_Min="min", Prix_Moyen="mean", Prix_Max="max", Nombre_Vols="count"
      )
      .reset_index()
  )

  # Arrondi du prix moyen à 2 décimales
  df_agg["Prix_Moyen"] = df_agg["Prix_Moyen"].round(2)

  # 5. Sauvegarde du résultat agrégé final
  df_agg.to_csv(output_file, index=False)
  print(
      f"Traitement et agrégation réussis. Fichier sauvegardé sous"
      f" {output_file}"
  )


if __name__ == "__main__":
  traiter_series_temporelles()
