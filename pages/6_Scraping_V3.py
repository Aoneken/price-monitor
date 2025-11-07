"""
Página de Scraping V3
Ejecuta scraping de precios usando el SDK V3
"""
import streamlit as st
from datetime import date, timedelta
import sys
from pathlib import Path

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler_v3 import ScraperScheduler
from src.persistence.database_adapter import DatabaseAdapter


st.set_page_config(
    page_title="Scraping V3",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Scraping Automático V3")
st.markdown("---")

# Sidebar con configuración
st.sidebar.header("⚙️ Configuración")

cache_hours = st.sidebar.slider(
    "Caché (horas)",
    min_value=1,
    max_value=72,
    value=24,
    help="No re-scrapear URLs scrapeadas en las últimas X horas"
)

days_ahead = st.sidebar.number_input(
    "Días hacia adelante",
    min_value=1,
    max_value=365,
    value=30,
    help="Check-in en X días desde hoy"
)

nights = st.sidebar.number_input(
    "Número de noches",
    min_value=1,
    max_value=30,
    value=2,
    help="Duración de la estadía"
)

headless = st.sidebar.checkbox(
    "Modo headless",
    value=True,
    help="Ejecutar navegador sin interfaz gráfica"
)

# Información de fechas
check_in = date.today() + timedelta(days=days_ahead)
check_out = check_in + timedelta(days=nights)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Check-in:** {check_in.strftime('%d/%m/%Y')}")
st.sidebar.markdown(f"**Check-out:** {check_out.strftime('%d/%m/%Y')}")
st.sidebar.markdown(f"**Noches:** {nights}")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📋 URLs Disponibles")
    
    # Inicializar adapter
    try:
        adapter = DatabaseAdapter()
        
        # Obtener URLs activas
        all_urls = adapter.get_active_urls()
        
        if not all_urls:
            st.warning("No hay URLs activas en la base de datos.")
            st.stop()
        
        # Agrupar por plataforma
        platforms = {}
        for url_data in all_urls:
            platform = url_data['plataforma']
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(url_data)
        
        # Mostrar contadores
        for platform, urls in platforms.items():
            st.metric(platform, len(urls))
        
        st.markdown(f"**Total URLs activas:** {len(all_urls)}")
        
        # URLs en caché
        recent = adapter.get_recent_scrapes(cache_hours)
        st.markdown(f"**URLs en caché ({cache_hours}h):** {len(recent)}")
        
        urls_to_scrape = [u for u in all_urls if u['id_plataforma_url'] not in recent]
        st.markdown(f"**URLs pendientes:** {len(urls_to_scrape)}")
        
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        st.stop()

with col2:
    st.header("🎯 Acciones")
    
    # Botón para scrapear todo
    if st.button("🚀 Scrapear Todo", type="primary", use_container_width=True):
        if len(urls_to_scrape) == 0:
            st.warning("No hay URLs pendientes (todas en caché)")
        else:
            with st.spinner(f"Scraping {len(urls_to_scrape)} URLs..."):
                try:
                    scheduler = ScraperScheduler(
                        cache_hours=cache_hours,
                        headless=headless
                    )
                    
                    # Ejecutar scraping
                    stats = scheduler.scrape_all(
                        days_ahead=days_ahead,
                        nights=nights
                    )
                    
                    # Mostrar resultados
                    st.success(f"✓ Scraping completado!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Procesadas", stats['total_urls'])
                    with col_b:
                        st.metric("Éxitos", stats['success'])
                    with col_c:
                        st.metric("Errores", stats['errors'])
                    
                    if stats['total_urls'] > 0:
                        success_rate = stats['success'] / stats['total_urls'] * 100
                        st.progress(success_rate / 100)
                        st.caption(f"Tasa de éxito: {success_rate:.1f}%")
                    
                    # Detalles
                    with st.expander("Ver detalles"):
                        for result in stats['results']:
                            status_icon = "✓" if result['status'] == 'success' else "✗"
                            st.write(f"{status_icon} {result['platform']} (URL {result['url_id']}): {result.get('nights_saved', 0)} noches")
                            if result.get('error'):
                                st.caption(f"   Error: {result['error']}")
                
                except Exception as e:
                    st.error(f"Error durante scraping: {e}")
    
    st.markdown("---")
    
    # Botones por plataforma
    st.subheader("Por plataforma")
    
    for platform in platforms.keys():
        platform_urls_pending = [
            u for u in urls_to_scrape 
            if u['plataforma'] == platform
        ]
        
        count = len(platform_urls_pending)
        disabled = count == 0
        
        if st.button(
            f"{platform} ({count})",
            key=f"btn_{platform}",
            disabled=disabled,
            use_container_width=True
        ):
            with st.spinner(f"Scraping {platform}..."):
                try:
                    scheduler = ScraperScheduler(
                        cache_hours=cache_hours,
                        headless=headless
                    )
                    
                    stats = scheduler.scrape_platform(
                        platform=platform,
                        days_ahead=days_ahead,
                        nights=nights
                    )
                    
                    st.success(f"✓ {platform} completado!")
                    st.metric("Éxitos", stats['success'])
                    st.metric("Errores", stats['errors'])
                
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("SDK V3 - Price Monitor | Scraping automático con Playwright")
