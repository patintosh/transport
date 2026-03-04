#!/bin/bash
echo "🚀 Génération de l'index..."
python3 generateur.py
echo "📦 Préparation des fichiers..."
git add .
echo "📤 Envoi vers GitHub..."
git commit -m "Mise à jour automatique le $(date +'%d/%m/%Y')"
git push
echo "✅ C'est en ligne !"