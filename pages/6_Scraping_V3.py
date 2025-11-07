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
    st.header("📋 Filtros de Scraping")
    
    # Inicializar adapter
    try:
        adapter = DatabaseAdapter()
        
        # Obtener URLs activas
        all_urls = adapter.get_active_urls()
        
        if not all_urls:
            st.warning("No hay URLs activas en la base de datos.")
            st.stop()
        
        # Agrupar por plataforma y establecimiento
        platforms = {}
        establecimientos = {}
        
        for url_data in all_urls:
            platform = url_data['plataforma']
            estab_id = url_data['id_establecimiento']
            
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(url_data)
            
            if estab_id not in establecimientos:
                # Obtener nombre del establecimiento de la BD
                establecimientos[estab_id] = {
                    'urls': [],
                    'nombre': f"Establecimiento #{estab_id}"  # Placeholder
                }
            establecimientos[estab_id]['urls'].append(url_data)
        
        # --- FILTROS PERSONALIZADOS ---
        st.subheader("🔍 Selecciona qué scrapear")
        
        # Filtro 1: Por Plataforma
        filter_platforms = st.multiselect(
            "Plataformas",
            options=list(platforms.keys()),
            default=list(platforms.keys()),
            help="Selecciona una o más plataformas"
        )
        
        # Filtro 2: Por Establecimiento (IDs)
        filter_establishments = st.multiselect(
            "Establecimientos (ID)",
            options=list(establecimientos.keys()),
            default=list(establecimientos.keys()),
            help="Selecciona uno o más establecimientos por ID"
        )
        
        # Filtro 3: Por URL específica
        url_options = {
            f"{u['plataforma']} - ID:{u['id_plataforma_url']} - {u['url'][:50]}...": u['id_plataforma_url']
            for u in all_urls
        }
        
        filter_urls = st.multiselect(
            "URLs específicas (opcional)",
            options=list(url_options.keys()),
            default=[],
            help="Deja vacío para usar filtros de plataforma/establecimiento"
        )
        
        # Aplicar filtros
        if filter_urls:
            # Si hay URLs específicas, usar solo esas
            selected_url_ids = [url_options[key] for key in filter_urls]
            urls_filtered = [u for u in all_urls if u['id_plataforma_url'] in selected_url_ids]
        else:
            # Filtrar por plataforma + establecimiento
            urls_filtered = [
                u for u in all_urls
                if u['plataforma'] in filter_platforms
                and u['id_establecimiento'] in filter_establishments
            ]
        
        # URLs en caché
        recent = adapter.get_recent_scrapes(cache_hours)
        
        # URLs pendientes (aplicando filtros)
        urls_to_scrape = [
            u for u in urls_filtered 
            if u['id_plataforma_url'] not in recent
        ]
        
        st.markdown("---")
        
        # Resumen de filtros
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("📊 Total URLs", len(all_urls))
        with col_b:
            st.metric("🎯 Filtradas", len(urls_filtered))
        with col_c:
            st.metric("⏳ Pendientes", len(urls_to_scrape))
        
        # Detalle por plataforma (filtrado)
        st.markdown("**Distribución por plataforma (filtradas):**")
        filtered_platforms = {}
        for url_data in urls_filtered:
            platform = url_data['plataforma']
            if platform not in filtered_platforms:
                filtered_platforms[platform] = 0
            filtered_platforms[platform] += 1
        
        cols = st.columns(len(filtered_platforms) if filtered_platforms else 1)
        for idx, (platform, count) in enumerate(filtered_platforms.items()):
            with cols[idx]:
                in_cache = len([u for u in urls_filtered if u['plataforma'] == platform and u['id_plataforma_url'] in recent])
                st.metric(platform, f"{count} ({count - in_cache} pend.)")
        
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        st.stop()

with col2:
    st.header("🎯 Acciones de Scraping")
    
    # Botón para scrapear selección
    if st.button("🚀 Scrapear Selección", type="primary", use_container_width=True):
        if len(urls_to_scrape) == 0:
            st.warning("No hay URLs pendientes en la selección")
        else:
            with st.spinner(f"Scraping {len(urls_to_scrape)} URLs..."):
                try:
                    scheduler = ScraperScheduler(
                        cache_hours=cache_hours,
                        headless=headless
                    )
                    
                    # Scrapear solo las URLs filtradas
                    results = []
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, url_data in enumerate(urls_to_scrape):
                        status_text.text(f"Scraping {url_data['plataforma']} (URL {url_data['id_plataforma_url']})...")
                        
                        result = scheduler.scrape_url(url_data, check_in, check_out)
                        results.append(result)
                        
                        if result['status'] == 'success':
                            success_count += 1
                        else:
                            error_count += 1
                        
                        progress_bar.progress((idx + 1) / len(urls_to_scrape))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Mostrar resultados
                    st.success(f"✓ Scraping completado!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Procesadas", len(urls_to_scrape))
                    with col_b:
                        st.metric("✓ Éxitos", success_count)
                    with col_c:
                        st.metric("✗ Errores", error_count)
                    
                    if len(urls_to_scrape) > 0:
                        success_rate = success_count / len(urls_to_scrape) * 100
                        st.progress(success_rate / 100)
                        st.caption(f"Tasa de éxito: {success_rate:.1f}%")
                    
                    # Detalles
                    with st.expander("📋 Ver detalles"):
                        for result in results:
                            status_icon = "✓" if result['status'] == 'success' else "✗"
                            st.write(f"{status_icon} **{result['platform']}** (URL {result['url_id']}): {result.get('nights_saved', 0)} noches")
                            if result.get('error'):
                                st.caption(f"   ⚠️ Error: {result['error']}")
                    
                    # Cleanup
                    if scheduler.orchestrator:
                        scheduler.orchestrator.cleanup()
                
                except Exception as e:
                    st.error(f"Error durante scraping: {e}")
    
    st.markdown("---")
    
    # Botón para ignorar caché
    st.subheader("🔄 Forzar Re-scraping")
    
    if st.button(
        "⚡ Scrapear Todo (Ignorar Caché)",
        help="Scrapea todas las URLs filtradas, incluso si están en caché",
        use_container_width=True
    ):
        if len(urls_filtered) == 0:
            st.warning("No hay URLs en la selección")
        else:
            with st.spinner(f"Scraping {len(urls_filtered)} URLs (forzado)..."):
                try:
                    scheduler = ScraperScheduler(
                        cache_hours=0,  # Ignorar caché
                        headless=headless
                    )
                    
                    results = []
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, url_data in enumerate(urls_filtered):
                        status_text.text(f"Scraping {url_data['plataforma']} (URL {url_data['id_plataforma_url']})...")
                        
                        result = scheduler.scrape_url(url_data, check_in, check_out)
                        results.append(result)
                        
                        if result['status'] == 'success':
                            success_count += 1
                        else:
                            error_count += 1
                        
                        progress_bar.progress((idx + 1) / len(urls_filtered))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.success(f"✓ Re-scraping completado!")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("✓ Éxitos", success_count)
                    with col_b:
                        st.metric("✗ Errores", error_count)
                    
                    # Cleanup
                    if scheduler.orchestrator:
                        scheduler.orchestrator.cleanup()
                
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("SDK V3 - Price Monitor | Scraping automático con Playwright")
