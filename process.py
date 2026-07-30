def traiter_series_temporelles():
    input_file = "vols_aircorsica.csv"
    output_file = "series_temporelles_j7.csv"

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_file} est introuvable.")
        return

    if df.empty:
        print("Le fichier CSV est vide — aucune donnée à traiter.")
        return

    if "Prix" not in df.columns:
        print("Erreur : Colonne 'Prix' introuvable.")
        return

    df["Prix_Numeric"] = df["Prix"].apply(clean_price)
    df = df.dropna(subset=["Prix_Numeric"])

    if df.empty:
        print("⚠️ Aucun prix valide — extraction probablement vide. Séries NON générées.")
        return

    # Normalisation date
    date_col = None
    for col in df.columns:
        if "date" in col.lower() or "capture" in col.lower():
            date_col = col
            break

    df["Date_Capture_Seule"] = pd.to_datetime(
        df[date_col], format="mixed", errors="coerce"
    ).dt.date

    df = df.dropna(subset=["Date_Capture_Seule"])

    group_cols = ["Date_Capture_Seule", "Départ", "Arrivée", "Date vol"]
    group_cols = [col for col in group_cols if col in df.columns]

    df_agg = (
        df.groupby(group_cols)["Prix_Numeric"]
        .agg(Prix_Min="min", Prix_Moyen="mean", Prix_Max="max", Nombre_Vols="count")
        .reset_index()
    )

    df_agg["Prix_Moyen"] = df_agg["Prix_Moyen"].round(2)
    df_agg.to_csv(output_file, index=False)

    print(f"Séries temporelles générées : {output_file}")
