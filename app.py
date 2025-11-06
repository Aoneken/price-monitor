"""
🏨 Price Monitor - Sistema de Monitoreo de Precios de Alojamientos
Aplicación web para monitorear y comparar precios entre plataformas
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurar path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager
from src.visualizer import PriceVisualizer

# Configuración de la página
st.set_page_config(
    page_title="Price Monitor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
    <style>
    /* Estilo general - OPTIMIZADO PARA ESPACIO */
    .main {
        padding-top: 1rem;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Títulos más estilizados - ESPACIADO REDUCIDO */
    h1 {
        color: #1f77b4;
        font-weight: 700;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 1rem;
        font-size: 2rem !important;
    }
    
    h2 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 1.5rem !important;
    }
    
    h3 {
        color: #34495e;
        font-weight: 500;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 1.2rem !important;
    }
    
    /* Métricas mejoradas - COMPACTAS */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.3rem 0;
    }
    
    .metric-label {
        font-size: 0.8rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Tarjetas de competidor - COMPACTAS */
    .competitor-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s;
    }
    
    .competitor-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Botones personalizados */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Alertas mejoradas - COMPACTAS */
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.75rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    /* Sidebar mejorado */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Tabs estilizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }
    
    /* Tabla mejorada */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Optimización de espacio adicional */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    div[data-testid="stExpander"] {
        margin: 0.5rem 0;
    }
    
    div[data-testid="column"] {
        padding: 0 0.5rem;
    }
    
    /* Reducir espacio en metrics de Streamlit */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)


# ==================== FUNCIONES AUXILIARES ====================

@st.cache_data
def load_competitors():
    """Carga la configuración de competidores"""
    config_path = 'config/competitors.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"properties": []}


def save_competitors(config):
    """Guarda la configuración de competidores"""
    config_path = 'config/competitors.json'
    os.makedirs('config', exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    # Limpiar caché para refrescar datos
    load_competitors.clear()


def format_price(price):
    """Formatea un precio en USD"""
    if price is None or pd.isna(price):
        return "N/A"
    return f"${price:,.2f}"


def get_platform_icon(platform):
    """Retorna el icono para cada plataforma"""
    icons = {
        'Airbnb': '🏠',
        'Booking': '🏨',
    }
    return icons.get(platform, '📊')


# ==================== COMPONENTES DE UI ====================

def render_sidebar():
    """Renderiza la barra lateral con navegación y configuración"""
    with st.sidebar:
        st.markdown("### 💰 Price Monitor")
        st.markdown("---")
        
        # Información rápida
        st.markdown("#### 📌 Información")
        
        config = load_competitors()
        total_properties = len(config.get('properties', []))
        
        st.metric("Competidores Registrados", total_properties)
        
        # Verificar si hay datos históricos
        data_manager = DataManager()
        df = data_manager.load_data()
        
        if df is not None and not df.empty:
            total_records = len(df)
            last_update = pd.to_datetime(df['scraped_at']).max()
            
            st.metric("Registros Totales", f"{total_records:,}")
            st.caption(f"Última actualización: {last_update.strftime('%d/%m/%Y %H:%M')}")
        else:
            st.info("No hay datos históricos aún")
        
        st.markdown("---")
        
        # Enlaces útiles
        st.markdown("#### 🔗 Enlaces")
        st.markdown("[📖 Documentación](QUICKSTART.md)")
        st.markdown("[🏗️ Arquitectura](ARCHITECTURE.md)")
        st.markdown("[📝 Ejemplos](EXAMPLES.md)")
        
        st.markdown("---")
        st.caption("v2.0 - Sistema de Monitoreo de Precios")


def render_dashboard():
    """Renderiza el dashboard principal con métricas y resumen"""
    st.markdown("## 📊 Dashboard General")
    
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df is None or df.empty:
        st.info("""
            👋 **¡Bienvenido al Price Monitor!**
            
            No hay datos disponibles todavía. Para empezar:
            1. Ve a la pestaña **"Gestión de Competidores"** para agregar propiedades
            2. Luego ve a **"Nuevo Scraping"** para obtener precios
            3. ¡Vuelve aquí para ver tus análisis!
        """)
        return
    
    # Convertir fechas
    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    df['checkin'] = pd.to_datetime(df['checkin'])
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Total de Registros</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(f"{len(df):,}"), unsafe_allow_html=True)
    
    with col2:
        unique_properties = df['property_name'].nunique()
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-label">Propiedades</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(unique_properties), unsafe_allow_html=True)
    
    with col3:
        avg_price = df[df['price_usd'].notna()]['price_usd'].mean()
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-label">Precio Promedio</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(format_price(avg_price)), unsafe_allow_html=True)
    
    with col4:
        last_scrape = df['scraped_at'].max()
        days_ago = (datetime.now() - last_scrape).days
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div class="metric-label">Último Scraping</div>
                <div class="metric-value">{}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">hace {} días</div>
            </div>
        """.format(last_scrape.strftime('%d/%m/%Y'), days_ago), unsafe_allow_html=True)
    
    # Gráficos resumidos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Evolución de Precios")
        
        # Gráfico de líneas por propiedad
        fig = go.Figure()
        
        for prop in df['property_name'].unique():
            prop_df = df[df['property_name'] == prop]
            prop_df = prop_df[prop_df['price_usd'].notna()].sort_values('checkin')
            
            if not prop_df.empty:
                fig.add_trace(go.Scatter(
                    x=prop_df['checkin'],
                    y=prop_df['price_usd'],
                    mode='lines+markers',
                    name=prop,
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Fecha: %{x|%d/%m/%Y}<br>' +
                                 'Precio: $%{y:,.2f}<br>' +
                                 '<extra></extra>'
                ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified',
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🏆 Comparación por Plataforma")
        
        # Datos válidos por plataforma
        platform_data = df[df['price_usd'].notna()].groupby('platform').agg({
            'price_usd': ['mean', 'min', 'max', 'count']
        }).round(2)
        
        fig = go.Figure()
        
        platforms = platform_data.index.tolist()
        
        fig.add_trace(go.Bar(
            x=platforms,
            y=platform_data['price_usd']['mean'],
            name='Precio Promedio',
            marker_color='#1f77b4',
            text=platform_data['price_usd']['mean'].apply(lambda x: f'${x:,.2f}'),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Promedio: $%{y:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            template='plotly_white',
            showlegend=False,
            yaxis_title="Precio (USD)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla resumen por propiedad
    st.markdown("### 📋 Resumen por Propiedad")
    
    summary = df[df['price_usd'].notna()].groupby('property_name').agg({
        'price_usd': ['min', 'max', 'mean'],
        'platform': 'count'
    }).round(2)
    
    summary.columns = ['Precio Mínimo (USD)', 'Precio Máximo (USD)', 'Precio Promedio (USD)', 'Total Registros']
    
    # Formatear precios
    for col in ['Precio Mínimo (USD)', 'Precio Máximo (USD)', 'Precio Promedio (USD)']:
        summary[col] = summary[col].apply(lambda x: f'${x:,.2f}')
    
    st.dataframe(summary, use_container_width=True)


def render_scraping_interface():
    """Interfaz para realizar nuevo scraping"""
    st.markdown("## � Nuevo Scraping")
    
    config = load_competitors()
    properties = config.get('properties', [])
    
    if not properties:
        st.warning("""
            ⚠️ **No hay competidores registrados**
            
            Ve a la pestaña "Gestión de Competidores" para agregar propiedades antes de realizar un scraping.
        """)
        return
    
    # Selector de propiedad
    property_names = [p['name'] for p in properties]
    selected_property = st.selectbox(
        "🏨 Selecciona una propiedad:",
        property_names,
        help="Elige el competidor del que quieres obtener precios"
    )
    
    # Encontrar la propiedad seleccionada
    property_config = next(p for p in properties if p['name'] == selected_property)
    
    # Mostrar información de la propiedad (compacto)
    platforms = property_config.get('platforms', {})
    platform_count = len(platforms)
    st.caption(f"📍 {platform_count} plataforma(s) configurada(s)")
    
    # Configuración de scraping
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📅 Configuración de Fechas**")
        
        # Rango de fechas
        start_date = st.date_input(
            "Fecha de inicio:",
            value=datetime.now(),
            min_value=datetime.now(),
            help="Primera fecha de check-in a consultar"
        )
        
        days_to_scrape = st.slider(
            "Días a scrapear:",
            min_value=1,
            max_value=30,
            value=7,
            help="Cantidad de días consecutivos desde la fecha de inicio"
        )
        
        end_date = start_date + timedelta(days=days_to_scrape - 1)
        
        st.caption(f"📊 {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')} ({days_to_scrape} días)")
    
    with col2:
        st.markdown("**👥 Configuración de Reserva**")
        
        guests = st.number_input(
            "Número de huéspedes:",
            min_value=1,
            max_value=16,
            value=2,
            help="Cantidad de personas que se alojarán"
        )
        
        nights = st.number_input(
            "Número de noches:",
            min_value=1,
            max_value=30,
            value=1,
            help="Duración de la estadía en noches"
        )
        
        st.caption(f"🛏️ {guests} huésped(es) × {nights} noche(s)")
    
    # Selector de plataformas
    st.markdown("**🔧 Plataformas**")
    
    platforms = property_config.get('platforms', {})
    
    col1, col2, col3 = st.columns(3)
    
    selected_platforms = {}
    
    with col1:
        if 'airbnb' in platforms:
            selected_platforms['airbnb'] = st.checkbox(
                "🏠 Airbnb",
                value=True,
                help="Obtener precios de Airbnb"
            )
    
    with col2:
        if 'booking' in platforms:
            selected_platforms['booking'] = st.checkbox(
                "🏨 Booking",
                value=True,
                help="Obtener precios de Booking.com"
            )
    
    if not any(selected_platforms.values()):
        st.warning("⚠️ Selecciona al menos una plataforma")
        return
    
    # Checkbox para forzar ejecución (ignora anti-duplicado)
    col_force, col_btn = st.columns([2, 1])
    
    with col_force:
        force_run = st.checkbox(
            "🔄 Forzar ejecución",
            value=False,
            help="Permite ejecutar el scraping incluso si existe una ejecución idéntica en las últimas 48 horas"
        )
    
    # Botón de scraping
    with col_btn:
        run_button = st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True)
    
    if run_button:
        run_scraping(
            property_config,
            selected_platforms,
            start_date,
            end_date,
            guests,
            nights,
            force_run
        )


def run_scraping(property_config, selected_platforms, start_date, end_date, guests, nights, force_run=False):
    """Ejecuta el proceso de scraping"""
    
    property_name = property_config['name']
    platforms = property_config.get('platforms', {})
    
    # Contenedor para progreso
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Scraping en Progreso...")
        
        # Verificar si ya existe una ejecución reciente con la misma configuración
        data_manager = DataManager()
        
        # Calcular plataformas seleccionadas
        active_platforms = [k for k, v in selected_platforms.items() if v]
        
        # Chequeo anti-duplicado (48 horas)
        is_recent = data_manager.is_recent_same_run(
            property_name=property_name,
            start_date=start_date,
            end_date=end_date,
            nights=nights,
            guests=guests,
            platforms=active_platforms,
            window_hours=48
        )
        
        if is_recent and not force_run:
            st.warning(f"""
                ⚠️ **Ejecución Duplicada Detectada**
                
                Ya existe un scraping con esta configuración para '{property_name}' realizado en las últimas 48 horas.
                
                - Propiedad: {property_name}
                - Fechas: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}
                - Noches: {nights}
                - Huéspedes: {guests}
                - Plataformas: {', '.join(active_platforms)}
                
                Para ejecutarlo de todas formas, marca la opción **"Forzar ejecución"** y vuelve a intentar.
            """)
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total_steps = sum(selected_platforms.values()) * 2  # *2 porque cada plataforma tiene inicio y fin
        current_step = 0
        
        # Scrapear Airbnb
        if selected_platforms.get('airbnb', False):
            status_text.markdown("🏠 **Scrapeando Airbnb...**")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            try:
                airbnb = AirbnbScraper()
                airbnb_results = airbnb.scrape_date_range(
                    platforms['airbnb'],
                    start_date,
                    end_date,
                    nights=nights,
                    guests=guests,
                    debug_first=False,  # Desactivado para evitar archivos debug
                    property_name=property_name  # Nombre para archivos debug únicos
                )
                results.extend(airbnb_results)
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                st.success(f"✅ Airbnb: {len(airbnb_results)} registros obtenidos")
            except Exception as e:
                st.error(f"❌ Error en Airbnb: {str(e)}")
        
        # Scrapear Booking
        if selected_platforms.get('booking', False):
            status_text.markdown("🏨 **Scrapeando Booking...**")
            current_step += 1
            progress_bar.progress(current_step / total_steps)
            
            try:
                booking = BookingScraper()
                booking_results = booking.scrape_date_range(
                    platforms['booking'],
                    start_date,
                    end_date,
                    nights=nights,
                    adults=guests,
                    debug_first=False,  # Desactivado para evitar archivos debug
                    property_name=property_name  # Nombre para archivos debug únicos
                )
                results.extend(booking_results)
                
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                st.success(f"✅ Booking: {len(booking_results)} registros obtenidos")
            except Exception as e:
                st.error(f"❌ Error en Booking: {str(e)}")
        
        # Guardar resultados
        if results:
            status_text.markdown("💾 **Guardando resultados...**")
            data_manager.save_results(results, property_name)
            
            # Registrar ejecución exitosa (log anti-duplicado)
            try:
                data_manager.log_scrape_run(
                    property_name=property_name,
                    start_date=start_date,
                    end_date=end_date,
                    nights=nights,
                    guests=guests,
                    platforms=active_platforms
                )
            except Exception as e:
                # No detener el flujo si falla el logging
                st.info(f"ℹ️ No se pudo registrar el log de ejecución: {e}")
            
            progress_bar.progress(1.0)
            
            st.markdown("""
                <div class="success-box">
                    <strong>✅ Scraping Completado Exitosamente</strong><br>
                    Se obtuvieron {} registros y fueron guardados correctamente.
                </div>
            """.format(len(results)), unsafe_allow_html=True)
            
            # Mostrar preview de resultados
            with st.expander("👀 Ver Resultados Obtenidos", expanded=True):
                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)
        else:
            st.warning("⚠️ No se obtuvieron resultados del scraping")


def render_historical_data():
    """Visualiza datos históricos con gráficos y análisis"""
    st.markdown("## 📈 Datos Históricos")
    
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df is None or df.empty:
        st.info("""
            📭 **No hay datos históricos disponibles**
            
            Realiza un scraping primero en la pestaña "Nuevo Scraping" para generar datos.
        """)
        return
    
    # Selector de propiedad
    properties = df['property_name'].unique().tolist()
    
    selected_property = st.selectbox(
        "🏨 Selecciona una propiedad:",
        properties,
        help="Elige la propiedad para ver sus datos históricos"
    )
    
    # Filtrar datos de la propiedad
    property_df = data_manager.get_property_data(selected_property)
    
    if property_df is None or property_df.empty:
        st.warning(f"No hay datos para '{selected_property}'")
        return
    
    # Estadísticas generales
    st.markdown("### 📊 Estadísticas")
    
    stats = data_manager.get_summary_stats(selected_property)
    
    if stats is not None and not stats.empty:
        # Mostrar estadísticas en tarjetas
        platforms = stats.index.tolist()
        cols = st.columns(len(platforms))
        
        for idx, platform in enumerate(platforms):
            with cols[idx]:
                st.markdown(f"### {get_platform_icon(platform)} {platform}")
                
                st.metric("Precio Mínimo", format_price(stats.loc[platform, 'Precio Mínimo']))
                st.metric("Precio Promedio", format_price(stats.loc[platform, 'Precio Promedio']))
                st.metric("Precio Máximo", format_price(stats.loc[platform, 'Precio Máximo']))
                st.metric("Total de Registros", int(stats.loc[platform, 'Cantidad Datos']))
    
    # Visualizaciones
    
    visualizer = PriceVisualizer()
    
    # Gráfico de comparación de precios
    st.markdown("### 📈 Evolución")
    
    fig_comparison = visualizer.create_price_comparison_chart(property_df, selected_property)
    if fig_comparison:
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Dos columnas para gráficos adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Diferencia de Precios**")
        fig_diff = visualizer.create_price_difference_chart(property_df, selected_property)
        if fig_diff:
            st.plotly_chart(fig_diff, use_container_width=True)
    
    with col2:
        st.markdown("**📦 Distribución**")
        fig_dist = visualizer.create_price_distribution(property_df, selected_property)
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True)
    
    # Tabla de datos
    st.markdown("### 📋 Datos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        platforms = property_df['platform'].unique().tolist()
        selected_platforms = st.multiselect(
            "Plataformas:",
            platforms,
            default=platforms
        )
    
    with col2:
        # Filtro de disponibilidad
        show_available_only = st.checkbox("Solo con precio", value=False)
    
    # Aplicar filtros
    filtered_df = property_df[property_df['platform'].isin(selected_platforms)].copy()
    
    if show_available_only:
        filtered_df = filtered_df[filtered_df['price_usd'].notna()]
    
    # Ordenar por fecha
    filtered_df = filtered_df.sort_values('checkin', ascending=False)
    
    # Mostrar tabla
    st.dataframe(filtered_df, use_container_width=True, height=350)
    
    # Botón de exportación
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Exportar a Excel", use_container_width=True):
            excel_path = data_manager.export_to_excel(selected_property)
            if excel_path:
                st.success(f"✅ Exportado a: {excel_path}")
    
    with col2:
        # Botón para descargar CSV
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"{selected_property}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_competitor_management():
    """Interfaz para gestionar competidores"""
    st.markdown("## 🏢 Gestión de Competidores")
    
    config = load_competitors()
    properties = config.get('properties', [])
    
    # Tabs para ver y agregar
    tab1, tab2 = st.tabs(["📋 Competidores Existentes", "➕ Agregar Nuevo"])
    
    with tab1:
        if not properties:
            st.info("""
                📭 **No hay competidores registrados**
                
                Ve a la pestaña "Agregar Nuevo" para crear tu primer competidor.
            """)
        else:
            st.markdown(f"**Total: {len(properties)} competidor(es)**")
            
            for idx, prop in enumerate(properties):
                with st.container():
                    st.markdown(f"""
                        <div class="competitor-card">
                            <h3>🏨 {prop['name']}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    platforms = prop.get('platforms', {})
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        for platform, url in platforms.items():
                            st.markdown(f"**{get_platform_icon(platform.title())} {platform.title()}:** [{url}]({url})")
                    
                    with col2:
                        if st.button(f"🗑️ Eliminar", key=f"delete_{idx}", use_container_width=True):
                            if st.session_state.get(f'confirm_delete_{idx}', False):
                                # Confirmar eliminación
                                properties.pop(idx)
                                config['properties'] = properties
                                save_competitors(config)
                                st.success(f"✅ '{prop['name']}' eliminado")
                                st.rerun()
                            else:
                                # Primera vez, pedir confirmación
                                st.session_state[f'confirm_delete_{idx}'] = True
                                st.warning("⚠️ Haz clic de nuevo para confirmar")
    
    with tab2:
        st.markdown("**➕ Agregar Nuevo Competidor**")
        
        with st.form("add_competitor_form"):
            property_name = st.text_input(
                "🏨 Nombre de la Propiedad:",
                placeholder="Ej: Aizeder Eco Container House",
                help="Un nombre único para identificar esta propiedad"
            )
            
            st.markdown("#### 🔗 URLs de Plataformas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                airbnb_url = st.text_input(
                    "🏠 URL de Airbnb:",
                    placeholder="https://www.airbnb.com/rooms/...",
                    help="URL completa de la propiedad en Airbnb (opcional)"
                )
            
            with col2:
                booking_url = st.text_input(
                    "🏨 URL de Booking:",
                    placeholder="https://www.booking.com/hotel/...",
                    help="URL completa de la propiedad en Booking (opcional)"
                )
            
            submitted = st.form_submit_button("💾 Guardar Competidor", use_container_width=True)
            
            if submitted:
                # Validaciones
                if not property_name.strip():
                    st.error("❌ El nombre de la propiedad es obligatorio")
                elif not airbnb_url.strip() and not booking_url.strip():
                    st.error("❌ Debes proporcionar al menos una URL (Airbnb o Booking)")
                else:
                    # Verificar que no exista ya
                    if any(p['name'] == property_name for p in properties):
                        st.error(f"❌ Ya existe un competidor con el nombre '{property_name}'")
                    else:
                        # Crear nueva propiedad
                        new_property = {
                            "name": property_name.strip(),
                            "platforms": {}
                        }
                        
                        if airbnb_url.strip():
                            new_property['platforms']['airbnb'] = airbnb_url.strip()
                        
                        if booking_url.strip():
                            new_property['platforms']['booking'] = booking_url.strip()
                        
                        # Agregar y guardar
                        properties.append(new_property)
                        config['properties'] = properties
                        save_competitors(config)
                        
                        st.markdown("""
                            <div class="success-box">
                                <strong>✅ Competidor Agregado Exitosamente</strong><br>
                                Ya puedes realizar scraping de esta propiedad.
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.balloons()
                        
                        # Limpiar formulario (esto se hará al recargar)
                        st.rerun()


# ==================== APLICACIÓN PRINCIPAL ====================

def main():
    """Función principal de la aplicación"""
    
    # Renderizar sidebar
    render_sidebar()
    
    # Header principal
    st.markdown("# 💰 Price Monitor")
    st.caption("Sistema Inteligente de Monitoreo de Precios de Alojamientos")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🔍 Nuevo Scraping",
        "📈 Datos Históricos",
        "🏢 Gestión de Competidores"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_scraping_interface()
    
    with tab3:
        render_historical_data()
    
    with tab4:
        render_competitor_management()


if __name__ == '__main__':
    main()
