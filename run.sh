#!/bin/bash

echo "🚀 Iniciando Price Monitor..."
echo ""
echo "La aplicación se abrirá en tu navegador."
echo "Si no se abre automáticamente, ve a: http://localhost:8501"
echo ""
echo "Presiona Ctrl+C para detener la aplicación."
echo ""
echo "---"
echo ""

# Lanzar Streamlit
streamlit run app.py --server.headless true
