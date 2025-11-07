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

# Configuración en columnas (más compacto)
col_conf1, col_conf2, col_conf3, col_conf4 = st.columns(4)

with col_conf1:
    cache_hours = st.number_input("⏱️ Caché (h)", min_value=0, max_value=72, value=24, help="0 = Ignorar caché")

with col_conf2:
    # Selector de fechas
    check_in = st.date_input("📅 Check-in", value=date.today() + timedelta(days=30))

with col_conf3:
    check_out = st.date_input("📅 Check-out", value=date.today() + timedelta(days=32))

with col_conf4:
    headless = st.checkbox("🔇 Headless", value=True, help="Navegador sin GUI")

# Calcular noches
nights = (check_out - check_in).days
if nights <= 0:
    st.error("❌ La fecha de check-out debe ser posterior al check-in")
    st.stop()

st.markdown(f"**Estadía:** {nights} noche(s) | {check_in.strftime('%d/%m/%Y')} → {check_out.strftime('%d/%m/%Y')}")
st.markdown("---")

# Main content (compacto)
st.subheader("� Filtros de Scraping")

# Inicializar adapter
try:
    adapter = DatabaseAdapter()
    
    # Obtener URLs activas
    all_urls = adapter.get_active_urls()
    
    if not all_urls:
        st.warning("No hay URLs activas en la base de datos.")
        st.stop()
    
    # Obtener nombres de establecimientos
    import sqlite3
    from pathlib import Path
    DB_PATH = Path(__file__).parent.parent / "database" / "price_monitor.db"
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT id_establecimiento, nombre_personalizado FROM Establecimientos")
    establecimientos_dict = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
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
            establecimientos[estab_id] = {
                'urls': [],
                'nombre': establecimientos_dict.get(estab_id, f"Establecimiento #{estab_id}")
            }
        establecimientos[estab_id]['urls'].append(url_data)
    
    # --- FILTROS COMPACTOS EN 3 COLUMNAS ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        filter_platforms = st.multiselect(
            "🏢 Plataformas",
            options=list(platforms.keys()),
            default=list(platforms.keys())
        )
    
    with col_f2:
        # Filtro por establecimiento con nombres
        estab_options = {
            f"{establecimientos[eid]['nombre']} (ID:{eid})": eid 
            for eid in establecimientos.keys()
        }
        filter_establishments_display = st.multiselect(
            "🏨 Establecimientos",
            options=list(estab_options.keys()),
            default=list(estab_options.keys())
        )
        filter_establishments = [estab_options[name] for name in filter_establishments_display]
    
    with col_f3:
        # Filtro por URL específica (opcional)
        url_options = {
            f"{u['plataforma']}-{establecimientos_dict.get(u['id_establecimiento'], 'N/A')[:20]}": u['id_plataforma_url']
            for u in all_urls
        }
        filter_urls_display = st.multiselect(
            "🔗 URLs específicas",
            options=list(url_options.keys()),
            default=[]
        )
        filter_urls = [url_options[name] for name in filter_urls_display]
        
    
    # Aplicar filtros
    if filter_urls:
        # Si hay URLs específicas, usar solo esas
        urls_filtered = [u for u in all_urls if u['id_plataforma_url'] in filter_urls]
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
    
    # Resumen compacto en métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("📊 Total", len(all_urls))
    with col_m2:
        st.metric("🎯 Filtradas", len(urls_filtered))
    with col_m3:
        st.metric("⏳ Pendientes", len(urls_to_scrape))
    with col_m4:
        cached = len([u for u in urls_filtered if u['id_plataforma_url'] in recent])
        st.metric("💾 En caché", cached)
    
    st.markdown("---")

except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# Botones de acción compactos
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    # Botón para scrapear selección
    if st.button("🚀 Scrapear Pendientes", type="primary", use_container_width=True):
        if len(urls_to_scrape) == 0:
            st.warning("No hay URLs pendientes")
        else:
            with st.spinner(f"Scraping {len(urls_to_scrape)} URLs..."):
                try:
                    scheduler = ScraperScheduler(cache_hours=cache_hours, headless=headless)
                    
                    results = []
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, url_data in enumerate(urls_to_scrape):
                        status_text.text(f"⏳ {url_data['plataforma']} - {establecimientos_dict.get(url_data['id_establecimiento'], 'N/A')[:20]}")
                        
                        result = scheduler.scrape_url(url_data, check_in, check_out)
                        results.append(result)
                        
                        if result['status'] == 'success':
                            success_count += 1
                        else:
                            error_count += 1
                        
                        progress_bar.progress((idx + 1) / len(urls_to_scrape))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.success(f"✓ Completado: {success_count} éxitos, {error_count} errores")
                    
                    if scheduler.orchestrator:
                        scheduler.orchestrator.cleanup()
                
                except Exception as e:
                    st.error(f"Error: {e}")

with col_btn2:
    # Forzar re-scraping
    if st.button("⚡ Forzar Todas", help="Ignora caché", use_container_width=True):
        if len(urls_filtered) == 0:
            st.warning("No hay URLs filtradas")
        else:
            with st.spinner(f"Scraping {len(urls_filtered)} URLs..."):
                try:
                    scheduler = ScraperScheduler(cache_hours=0, headless=headless)
                    
                    results = []
                    success_count = 0
                    
                    progress_bar = st.progress(0)
                    
                    for idx, url_data in enumerate(urls_filtered):
                        result = scheduler.scrape_url(url_data, check_in, check_out)
                        if result['status'] == 'success':
                            success_count += 1
                        progress_bar.progress((idx + 1) / len(urls_filtered))
                    
                    progress_bar.empty()
                    st.success(f"✓ {success_count}/{len(urls_filtered)} éxitos")
                    
                    if scheduler.orchestrator:
                        scheduler.orchestrator.cleanup()
                
                except Exception as e:
                    st.error(f"Error: {e}")

with col_btn3:
    # Ver detalles de selección
    with st.expander("📋 Ver selección actual"):
        if urls_to_scrape:
            for url_data in urls_to_scrape[:10]:  # Máximo 10
                st.caption(f"• {url_data['plataforma']} - {establecimientos_dict.get(url_data['id_establecimiento'], 'N/A')}")
            if len(urls_to_scrape) > 10:
                st.caption(f"... y {len(urls_to_scrape) - 10} más")
        else:
            st.caption("Sin URLs pendientes")

# Footer compacto
st.markdown("---")
st.caption("SDK V3 - Price Monitor")
