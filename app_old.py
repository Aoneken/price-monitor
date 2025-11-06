"""
🎯 Monitor de Precios - Airbnb vs Booking
Aplicación para comparar precios entre plataformas
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Importar módulos locales
from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager
from src.visualizer import PriceVisualizer

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Monitor de Precios",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZADO - ESTILO MODERNO SPA
# ============================================================================

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container principal */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Títulos con gradiente */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem !important;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 700;
        font-size: 1.8rem !important;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600;
        font-size: 1.3rem !important;
        margin-bottom: 0.8rem;
    }
    
    /* Tabs modernos */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #edf2f7;
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #4a5568;
        background-color: transparent;
        transition: all 0.2s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Botones mejorados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.5);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: white;
        padding: 2rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def load_config():
    """Carga la configuración de competidores"""
    config_path = 'config/competitors.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"competitors": []}

def save_config(config):
    """Guarda la configuración de competidores"""
    config_path = 'config/competitors.json'
    os.makedirs('config', exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# ============================================================================
# INICIALIZACIÓN DE SESIÓN
# ============================================================================

if 'config' not in st.session_state:
    st.session_state.config = load_config()

if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False

# ============================================================================
# SIDEBAR - GESTIÓN DE COMPETIDORES
# ============================================================================

with st.sidebar:
    st.markdown("### 🏠 Gestión de Competidores")
    st.markdown("---")
    
    # Mostrar competidores existentes
    if st.session_state.config.get('competitors'):
        st.markdown("#### 📋 Competidores Actuales")
        
        for idx, comp in enumerate(st.session_state.config['competitors']):
            with st.expander(f"🏡 {comp['name']}", expanded=False):
                st.markdown(f"**Airbnb:** `{comp['airbnb_url'][:40]}...`")
                st.markdown(f"**Booking:** `{comp['booking_url'][:40]}...`")
                
                if st.button("🗑️ Eliminar", key=f"delete_{idx}"):
                    st.session_state.config['competitors'].pop(idx)
                    save_config(st.session_state.config)
                    st.rerun()
    
    st.markdown("---")
    st.markdown("#### ➕ Agregar Nuevo Competidor")
    
    with st.form("add_competitor"):
        new_name = st.text_input("Nombre del alojamiento", placeholder="Ej: Casa de Playa")
        new_airbnb = st.text_input("URL de Airbnb", placeholder="https://www.airbnb.com.ar/rooms/...")
        new_booking = st.text_input("URL de Booking", placeholder="https://www.booking.com/hotel/...")
        
        submitted = st.form_submit_button("➕ Agregar Competidor")
        
        if submitted:
            if new_name and new_airbnb and new_booking:
                new_comp = {
                    "name": new_name,
                    "airbnb_url": new_airbnb,
                    "booking_url": new_booking
                }
                
                if 'competitors' not in st.session_state.config:
                    st.session_state.config['competitors'] = []
                
                st.session_state.config['competitors'].append(new_comp)
                save_config(st.session_state.config)
                st.success(f"✅ {new_name} agregado correctamente")
                st.rerun()
            else:
                st.error("⚠️ Completa todos los campos")
    
    st.markdown("---")
    st.markdown("### ℹ️ Acerca de")
    st.markdown("""
    **Monitor de Precios v2.0**
    
    Compara precios entre Airbnb y Booking automáticamente.
    
    - 🔍 Scraping inteligente
    - 📊 Visualizaciones interactivas
    - 💾 Historial de precios
    - 🎯 Múltiples competidores
    """)

# ============================================================================
# CONTENIDO PRINCIPAL
# ============================================================================

# Título principal
st.markdown("# 💰 Monitor de Precios")
st.markdown("### Compara precios entre Airbnb y Booking en tiempo real")
st.markdown("---")

# Crear tabs para navegación tipo SPA
tab1, tab2, tab3 = st.tabs(["🔍 Nuevo Análisis", "📊 Visualizaciones", "📁 Datos Históricos"])

# ============================================================================
# TAB 1: NUEVO ANÁLISIS
# ============================================================================

with tab1:
    st.markdown("## 🎯 Configurar Nueva Búsqueda")
    
    # Selección de competidor
    competitors = st.session_state.config.get('competitors', [])
    
    if not competitors:
        st.warning("⚠️ No hay competidores configurados. Agrega uno en el menú lateral.")
    else:
        selected_comp_name = st.selectbox(
            "Selecciona el alojamiento a analizar:",
            options=[comp['name'] for comp in competitors],
            key="comp_selector"
        )
        
        selected_comp = next(comp for comp in competitors if comp['name'] == selected_comp_name)
        
        # Parámetros de búsqueda
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_date = st.date_input(
                "📅 Fecha de inicio",
                value=datetime.now() + timedelta(days=1),
                min_value=datetime.now(),
                key="start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "📅 Fecha de fin",
                value=datetime.now() + timedelta(days=8),
                min_value=datetime.now(),
                key="end_date"
            )
        
        with col3:
            guests = st.number_input(
                "👥 Número de huéspedes",
                min_value=1,
                max_value=10,
                value=2,
                key="guests"
            )
        
        nights = st.number_input(
            "🌙 Noches por reserva",
            min_value=1,
            max_value=30,
            value=2,
            help="Cuántas noches durará cada reserva",
            key="nights"
        )
        
        # Botón de scraping
        st.markdown("---")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            if st.button("▶️ INICIAR SCRAPING", key="start_scraping", disabled=st.session_state.scraping_in_progress):
                if start_date >= end_date:
                    st.error("❌ La fecha de fin debe ser posterior a la fecha de inicio")
                else:
                    st.session_state.scraping_in_progress = True
                    
                    # Contenedor para el progreso
                    progress_container = st.container()
                    
                    with progress_container:
                        st.markdown("### 🔄 Scraping en progreso...")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Inicializar scrapers
                        airbnb_scraper = AirbnbScraper()
                        booking_scraper = BookingScraper()
                        data_manager = DataManager()
                        
                        # Calcular total de scrapings
                        date_range = (end_date - start_date).days + 1
                        total_scrapings = date_range * 2  # Airbnb + Booking
                        current_scraping = 0
                        
                        # Scrapear Airbnb
                        status_text.markdown("🔍 **Scrapeando Airbnb...**")
                        airbnb_results = airbnb_scraper.scrape_date_range(
                            selected_comp['airbnb_url'],
                            start_date,
                            end_date,
                            nights=nights,
                            guests=guests,
                            debug_first=True
                        )
                        
                        for result in airbnb_results:
                            result['property_name'] = selected_comp['name']
                            data_manager.save_price(result)
                            current_scraping += 1
                            progress_bar.progress(current_scraping / total_scrapings)
                        
                        # Scrapear Booking
                        status_text.markdown("🔍 **Scrapeando Booking...**")
                        booking_results = booking_scraper.scrape_date_range(
                            selected_comp['booking_url'],
                            start_date,
                            end_date,
                            nights=nights,
                            guests=guests,
                            debug_first=True
                        )
                        
                        for result in booking_results:
                            result['property_name'] = selected_comp['name']
                            data_manager.save_price(result)
                            current_scraping += 1
                            progress_bar.progress(current_scraping / total_scrapings)
                        
                        progress_bar.progress(1.0)
                        status_text.markdown("✅ **Scraping completado!**")
                        
                        # Mostrar resumen
                        st.success(f"✅ Scraping completado: {len(airbnb_results)} resultados de Airbnb, {len(booking_results)} de Booking")
                        
                        # Estadísticas rápidas
                        airbnb_success = sum(1 for r in airbnb_results if r.get('price_usd'))
                        booking_success = sum(1 for r in booking_results if r.get('price_usd'))
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        
                        with col_stat1:
                            st.metric("📊 Airbnb", f"{airbnb_success}/{len(airbnb_results)}", "precios encontrados")
                        
                        with col_stat2:
                            st.metric("📊 Booking", f"{booking_success}/{len(booking_results)}", "precios encontrados")
                        
                        with col_stat3:
                            total_success = airbnb_success + booking_success
                            st.metric("📊 Total", f"{total_success}/{total_scrapings}", "éxitos")
                    
                    st.session_state.scraping_in_progress = False

# ============================================================================
# TAB 2: VISUALIZACIONES
# ============================================================================

with tab2:
    st.markdown("## 📊 Análisis Visual de Precios")
    
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df.empty:
        st.info("📭 No hay datos para visualizar. Realiza un scraping primero.")
    else:
        # Filtros
        st.markdown("### 🔧 Filtros")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            properties = df['property_name'].unique().tolist()
            selected_property = st.selectbox("🏠 Alojamiento", options=properties)
        
        with col_f2:
            min_date = pd.to_datetime(df['checkin']).min().date()
            max_date = pd.to_datetime(df['checkin']).max().date()
            filter_start = st.date_input("Desde", value=min_date, min_value=min_date, max_value=max_date)
        
        with col_f3:
            filter_end = st.date_input("Hasta", value=max_date, min_value=min_date, max_value=max_date)
        
        # Filtrar datos
        df_filtered = df[
            (df['property_name'] == selected_property) &
            (pd.to_datetime(df['checkin']) >= pd.to_datetime(filter_start)) &
            (pd.to_datetime(df['checkin']) <= pd.to_datetime(filter_end))
        ]
        
        if df_filtered.empty:
            st.warning("No hay datos para los filtros seleccionados")
        else:
            # Métricas principales
            st.markdown("---")
            st.markdown("### 📈 Métricas Principales")
            
            airbnb_data = df_filtered[df_filtered['platform'] == 'Airbnb']
            booking_data = df_filtered[df_filtered['platform'] == 'Booking']
            
            airbnb_avg = airbnb_data['price_usd'].mean()
            booking_avg = booking_data['price_usd'].mean()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Airbnb Promedio", f"${airbnb_avg:.2f}" if not pd.isna(airbnb_avg) else "N/A")
            
            with col_m2:
                st.metric("Booking Promedio", f"${booking_avg:.2f}" if not pd.isna(booking_avg) else "N/A")
            
            with col_m3:
                if not pd.isna(airbnb_avg) and not pd.isna(booking_avg):
                    diff = airbnb_avg - booking_avg
                    st.metric("Diferencia", f"${diff:.2f}", f"{(diff/booking_avg)*100:.1f}%")
                else:
                    st.metric("Diferencia", "N/A")
            
            with col_m4:
                total_prices = len(df_filtered[df_filtered['price_usd'].notna()])
                st.metric("Precios Encontrados", f"{total_prices}/{len(df_filtered)}")
            
            # Gráficas
            st.markdown("---")
            visualizer = PriceVisualizer()
            
            # Gráfica de comparación
            st.markdown("### 📊 Comparación de Precios por Fecha")
            fig_comparison = visualizer.create_price_comparison_chart(df_filtered, selected_property)
            if fig_comparison:
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Gráfica de diferencias
            st.markdown("### 📉 Diferencia de Precios (Airbnb - Booking)")
            fig_diff = visualizer.create_price_difference_chart(df_filtered)
            if fig_diff:
                st.plotly_chart(fig_diff, use_container_width=True)
            
            # Distribución de precios
            col_dist1, col_dist2 = st.columns(2)
            
            with col_dist1:
                st.markdown("### 📊 Distribución Airbnb")
                fig_airbnb_dist = visualizer.create_price_distribution(airbnb_data, "Airbnb")
                if fig_airbnb_dist:
                    st.plotly_chart(fig_airbnb_dist, use_container_width=True)
            
            with col_dist2:
                st.markdown("### 📊 Distribución Booking")
                fig_booking_dist = visualizer.create_price_distribution(booking_data, "Booking")
                if fig_booking_dist:
                    st.plotly_chart(fig_booking_dist, use_container_width=True)

# ============================================================================
# TAB 3: DATOS HISTÓRICOS
# ============================================================================

with tab3:
    st.markdown("## 📁 Explorar Datos Históricos")
    
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df.empty:
        st.info("📭 No hay datos históricos aún.")
    else:
        # Estadísticas generales
        st.markdown("### 📊 Resumen General")
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            st.metric("Total de Registros", len(df))
        
        with col_s2:
            properties_count = df['property_name'].nunique()
            st.metric("Alojamientos", properties_count)
        
        with col_s3:
            success_rate = (df['price_usd'].notna().sum() / len(df)) * 100
            st.metric("Tasa de Éxito", f"{success_rate:.1f}%")
        
        with col_s4:
            date_range = (pd.to_datetime(df['checkin']).max() - pd.to_datetime(df['checkin']).min()).days
            st.metric("Rango de Fechas", f"{date_range} días")
        
        st.markdown("---")
        
        # Tabla de datos
        st.markdown("### 📋 Tabla de Datos")
        
        # Preparar datos para mostrar
        df_display = df.copy()
        df_display['checkin'] = pd.to_datetime(df_display['checkin']).dt.strftime('%Y-%m-%d')
        df_display['checkout'] = pd.to_datetime(df_display['checkout']).dt.strftime('%Y-%m-%d')
        df_display['scraped_at'] = pd.to_datetime(df_display['scraped_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Reordenar columnas
        columns_order = ['property_name', 'platform', 'checkin', 'checkout', 'price_usd', 'guests', 'scraped_at', 'error']
        df_display = df_display[columns_order]
        
        # Renombrar columnas para mejor lectura
        df_display.columns = ['Alojamiento', 'Plataforma', 'Check-in', 'Check-out', 'Precio USD', 'Huéspedes', 'Scrapeado', 'Error']
        
        st.dataframe(
            df_display,
            hide_index=True
        )
        
        # Opciones de exportación
        st.markdown("---")
        st.markdown("### 💾 Exportar Datos")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"precios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        
        with col_exp2:
            excel_path = data_manager.export_to_excel()
            if excel_path and os.path.exists(excel_path):
                with open(excel_path, 'rb') as f:
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=f,
                        file_name=os.path.basename(excel_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
        
        with col_exp3:
            if st.button("🗑️ Limpiar Todos los Datos"):
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("⚠️ Sí, Borrar Todo"):
                        if os.path.exists('data/price_history.csv'):
                            os.remove('data/price_history.csv')
                            st.success("✅ Datos eliminados")
                            st.rerun()
