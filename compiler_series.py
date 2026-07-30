import pandas as pd
import os
from datetime import datetime

def compiler_et_filtrer(chemin_fichier="vols_aircorsica.csv"):
    if not os.path.exists(chemin_fichier):
        print("❌ Fichier CSV introuvable.")
        return

    df = pd.read_csv(chemin_fichier)
    
    # Conversion des dates pour application du filtre (>= 7 jours d'avance)
    try:
        df['dt_capture'] = pd.to_datetime(df['Date de capture'], errors='coerce')
        df['dt_vol'] = pd.to_datetime(df['Date vol'], errors='coerce', dayfirst=True)
        
        # Calcul de l'anticipation en jours
        df['Jours_Avance'] = (df['dt_vol'] - df['dt_capture']).dt.days
        
        # Filtrer uniquement les observations faites au moins 7 jours à l'avance
        df_filtre = df[df['Jours_Avance'] >= 7].copy()
    except Exception as e:
        print(f"⚠️ Erreur lors du traitement des dates, application d'un filtre souple : {e}")
        df_filtre = df.copy()

    # Extraction de la valeur numérique du prix TTC pour les calculs
    df_filtre['Prix_num'] = df_filtre['Prix'].astype(str).str.extract(r'(\d+[.,]?\d*)')[0].str.replace(',', '.').astype(float)

    print(f"\n📊 --- COMPILATION DES SÉRIES CHRONOLOGIQUES (Anticipation >= 7 jours) ---")
    print(f"Nombre total de relevés éligibles : {len(df_filtre)}\n")

    # Regroupement par liaison et par date de vol pour analyser l'évolution
    if not df_filtre.empty:
        resume_liaisons = df_filtre.groupby(["Départ", "Arrivée", "Date vol"])['Prix_num'].agg(
            Relevés="count",
            Prix_Min="min",
            Prix_Moyen="mean",
            Prix_Max="max"
        ).reset_index()

        # Arrondi des prix
        resume_liaisons['Prix_Min'] = resume_liaisons['Prix_Min'].round(2)
        resume_liaisons['Prix_Moyen'] = resume_liaisons['Prix_Moyen'].round(2)
        resume_liaisons['Prix_Max'] = resume_liaisons['Prix_Max'].round(2)

        print(resume_liaisons.to_string(index=False))
        
        # Sauvegarde d'une vue consolidée des séries
        resume_liaisons.to_csv("series_chronologiques_vols.csv", index=False, encoding="utf-8-sig")
        print("\n💾 Série chronologique compilée enregistrée dans 'series_chronologiques_vols.csv'.")
    else:
        print("⚠️ Aucun vol ne correspond actuellement au filtre d'une semaine d'anticipation.")

if __name__ == "__main__":
    compiler_et_filtrer()