#!/bin/bash

echo "🚀 Instalando Price Monitor..."
echo ""

# Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

echo ""
echo "🌐 Instalando navegador Chromium para Playwright..."
playwright install chromium

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para iniciar la aplicación, ejecuta:"
echo "  streamlit run app.py"
echo ""
