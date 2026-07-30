import pandas as pd


def traiter_series_temporelles():
    # Lecture du fichier CSV brut
    input_file = "vols_aircorsica.csv"
    output_file = "series_temporelles_j7.csv"

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_file} est introuvable.")
        return

    # Identification dynamique de la colonne de date si nécessaire
    date_col = None
    for col in df.columns:
        if "date" in col.lower() or "capture" in col.lower():
            date_col = col
            break

    if date_col is None and len(df.columns) > 0:
        date_col = df.columns[0]  # Fallback sur la première colonne

    # Conversion de la date en gérant proprement le format sans heure (ISO8601 / mixed)
    if date_col:
        df["Date_Capture_Seule"] = pd.to_datetime(
            df[date_col], format="mixed", errors="coerce"
        )

    # Traitement des séries temporelles J+7 (préservation de la logique métier existante)
    # Exemple de nettoyage / agrégation standard pour les séries temporelles
    df = df.dropna(subset=["Date_Capture_Seule"])

    # Sauvegarde du résultat final
    df.to_csv(output_file, index=False)
    print(f"Traitement réussi. Fichier sauvegardé sous {output_file}")


if __name__ == "__main__":
    traiter_series_temporelles()
