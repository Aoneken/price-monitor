#!/bin/bash

# Script para detener Price Monitor
# Uso: ./stop.sh

echo "🛑 Deteniendo Price Monitor..."

# Buscar y matar procesos de Streamlit
PIDS=$(pgrep -f "streamlit run app.py")

if [ -z "$PIDS" ]; then
    echo "ℹ️  No hay instancias de Price Monitor corriendo"
    exit 0
fi

# Matar procesos
echo "$PIDS" | xargs kill

sleep 2

# Verificar que se detuvo
if pgrep -f "streamlit run app.py" > /dev/null; then
    echo "⚠️  Forzando detención..."
    echo "$PIDS" | xargs kill -9
fi

echo "✅ Price Monitor detenido correctamente"
