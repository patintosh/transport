import pandas as pd
import os

def nettoyer_csv(chemin_fichier="vols_aircorsica.csv"):
    if not os.path.exists(chemin_fichier):
        print("❌ Aucun fichier CSV trouvé à nettoyer.")
        return

    print("🧹 Nettoyage, normalisation et suppression des erreurs...")
    df = pd.read_csv(chemin_fichier)

    # Uniformisation des noms de colonnes historiques
    mapping_colonnes = {
        "Date_Scraping": "Date de capture",
        "Date_Vol": "Date vol"
    }
    df = df.rename(columns=mapping_colonnes)

    colonnes_attendues = ["Date de capture", "Départ", "Arrivée", "Date vol", "Horaire", "Prix"]
    
    for col in colonnes_attendues:
        if col not in df.columns:
            df[col] = "Inconnu"

    df = df[colonnes_attendues]

    # Suppression des lignes où le départ ou l'arrivée sont inconnus ou vides
    df = df[
        (df['Départ'].notna()) & (df['Départ'] != 'Inconnu') &
        (df['Arrivée'].notna()) & (df['Arrivée'] != 'Inconnu')
    ]

    # Remplacement des valeurs vides (NaN) par des valeurs par défaut propres
    df['Date vol'] = df['Date vol'].fillna('05/08/2026')
    df['Horaire'] = df['Horaire'].fillna('Inconnu')

    # Nettoyage des prix (extraction de la valeur numérique TTC)
    df = df.dropna(subset=["Prix"])
    df['Prix_num'] = df['Prix'].astype(str).str.extract(r'(\d+[.,]?\d*)')[0].str.replace(',', '.').astype(float)
    
    # Filtrage des prix aberrants
    df = df[(df['Prix_num'] >= 35) & (df['Prix_num'] <= 3000)]
    df = df.drop(columns=['Prix_num'])

    # Suppression des doublons stricts
    df = df.drop_duplicates(subset=["Date de capture", "Départ", "Arrivée", "Date vol", "Horaire", "Prix"])

    df.to_csv(chemin_fichier, index=False, encoding="utf-8-sig")
    print(f"✅ CSV nettoyé avec succès ! {len(df)} lignes valides conservées (0 valeur manquante).")

if __name__ == "__main__":
    nettoyer_csv()