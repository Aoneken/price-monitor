"""
Price Monitor - Aplicación Principal
Sistema de inteligencia de precios para plataformas de alojamiento
"""
import streamlit as st
from config.settings import STREAMLIT_CONFIG

# Configuración de la página
st.set_page_config(
    page_title=STREAMLIT_CONFIG['page_title'],
    page_icon=STREAMLIT_CONFIG['page_icon'],
    layout=STREAMLIT_CONFIG['layout'],
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">📊 Price Monitor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Sistema de Inteligencia de Precios para Plataformas de Alojamiento</div>',
    unsafe_allow_html=True
)

# Descripción de la aplicación
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="feature-box">
            <h3>🏠 Gestión de Establecimientos</h3>
            <p>Administra tu portafolio de propiedades y configura URLs de monitoreo en múltiples plataformas.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="feature-box">
            <h3>🤖 Scraping Automatizado</h3>
            <p>Extrae precios de Booking, Airbnb y más, con lógica inteligente de búsqueda y actualización.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="feature-box">
            <h3>📈 Análisis y Dashboard</h3>
            <p>Visualiza tendencias de precios, ocupación y obtén insights de tu competencia.</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# Instrucciones de uso
st.header("🚀 Cómo Empezar")

st.markdown("""
### Flujo de Trabajo Recomendado:

1. **📁 Establecimientos** (Pestaña 1)
   - Crea un nuevo establecimiento
   - Agrega URLs de Booking, Airbnb, etc.
   - Activa/desactiva monitoreo según necesites

2. **🔍 Scraping** (Pestaña 2)
   - Selecciona el establecimiento
   - Define el rango de fechas
   - Inicia el monitoreo y observa el progreso en tiempo real

3. **💾 Base de Datos** (Pestaña 3)
   - Explora todos los datos recolectados
   - Aplica filtros avanzados
   - Exporta a CSV para análisis externo

4. **📊 Dashboard** (Pestaña 4)
   - Visualiza gráficos de evolución de precios
   - Compara plataformas
   - Analiza tasas de ocupación

5. **🎯 Análisis** (Pestaña 5)
   - Funcionalidad futura: Comparación Cliente vs. Competidores
""")

st.divider()

# Footer con información del sistema
st.markdown("---")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Plataformas Soportadas", "Booking, Airbnb")

with col_b:
    st.metric("Lógica de Búsqueda", "3→2→1 Noches")

with col_c:
    st.metric("Actualización de Datos", "48 Horas")

# Información adicional
with st.expander("ℹ️ Información Técnica"):
    st.markdown("""
    ### Características Técnicas:
    
    - **Base de Datos**: SQLite con esquema normalizado
    - **Scraping**: Playwright con modo stealth anti-detección
    - **Arquitectura**: Strategy + Factory Pattern para escalabilidad
    - **Selectores**: Externalizados en JSON para fácil mantenimiento
    - **Lógica 48h**: Solo actualiza datos antiguos (> 48 horas)
    - **Rate Limiting**: Esperas aleatorias (3-8s) para evitar bloqueos
    - **Retry Logic**: Exponential backoff en caso de errores
    
    ### Próximas Funcionalidades:
    - Soporte para Vrbo y más plataformas
    - Notificaciones automáticas de cambios de precio
    - Módulo de análisis de competencia
    - Recomendaciones de pricing con IA
    """)

st.info(
    "👈 **Usa el menú lateral** para navegar entre las diferentes secciones de la aplicación.",
    icon="ℹ️"
)
