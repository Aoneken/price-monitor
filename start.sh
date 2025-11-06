#!/bin/bash
# Script de inicio rápido para Price-Monitor
# Uso: ./start.sh

echo "🚀 Iniciando Price-Monitor..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
if [ ! -f "venv/.installed" ]; then
    echo "📥 Instalando dependencias..."
    pip install -q -r requirements.txt
    
    echo "🎭 Instalando Playwright..."
    playwright install chromium
    
    touch venv/.installed
    echo "✓ Dependencias instaladas"
else
    echo "✓ Dependencias ya instaladas"
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo .env..."
    cp .env.example .env
    echo "✓ Archivo .env creado"
fi

# Inicializar base de datos (se crea automáticamente al primer uso)
echo "✓ Base de datos configurada"

echo ""
echo "✅ ¡Todo listo!"
echo ""
echo "🌐 Iniciando aplicación en http://localhost:8501"
echo "💡 Presiona Ctrl+C para detener"
echo ""

# Iniciar Streamlit
streamlit run app.py
