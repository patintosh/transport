import os
import pandas as pd

def nettoyer_csv(chemin_fichier="vols_aircorsica.csv"):
    if not os.path.exists(chemin_fichier):
        print(f"⚠️ Le fichier {chemin_fichier} n'existe pas encore.")
        return

    try:
        df = pd.read_csv(chemin_fichier)
        if df.empty:
            print("⚠️ Le fichier CSV est vide.")
            return

        print(f"📊 Fichier chargé : {len(df)} lignes avant nettoyage.")

        # Suppression des doublons stricts pour éviter les redondances
        df = df.drop_duplicates()

        # Nettoyage des espaces superflus sur les colonnes textuelles existantes
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        # Sauvegarde du fichier nettoyé
        df.to_csv(chemin_fichier, index=False, encoding="utf-8-sig")
        print(f"✅ Nettoyage terminé avec succès : {len(df)} lignes conservées.")

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage du CSV : {e}")
        raise e

if __name__ == "__main__":
    nettoyer_csv()
