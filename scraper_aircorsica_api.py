name: Suivi mensuel des prix Air Corsica (46 liaisons)

on:
  schedule:
    - cron: "0 6 1 * *"   # 1er de chaque mois, 6h00 UTC
  workflow_dispatch:        # permet de le lancer manuellement depuis l'onglet Actions

permissions:
  contents: write            # nécessaire pour que le workflow puisse committer/pousser

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Récupérer le dépôt
        uses: actions/checkout@v4

      - name: Installer Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Installer les dépendances
        run: pip install requests

      - name: Lancer le scraper
        env:
          SERPAPI_KEY: ${{ secrets.SERPAPI_KEY }}
        run: python scraper_aircorsica_api.py

      - name: Committer les nouveaux résultats
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add routes_aircorsica/ historique_global_france.csv
          git diff --staged --quiet || git commit -m "Mise à jour mensuelle des prix ($(date +%Y-%m-%d))"
          git push