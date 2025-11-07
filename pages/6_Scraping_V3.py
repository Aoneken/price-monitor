"""
Página de Scraping V3
Ejecuta scraping de precios usando el SDK V3
"""
import streamlit as st
from datetime import date, timedelta
import sys
from pathlib import Path
import pandas as pd
import time

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scheduler_incremental_v3 import IncrementalScraperScheduler
from src.persistence.database_adapter import DatabaseAdapter


st.set_page_config(
    page_title="Scraping V3",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Scraping Automático V3")

# Inicializar session_state para persistencia
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'scraping_results' not in st.session_state:
    st.session_state.scraping_results = []
if 'scraping_filters' not in st.session_state:
    st.session_state.scraping_filters = None

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
    
    # Filtrar establecimientos que tengan al menos una URL en las plataformas seleccionadas
    establecimientos_validos = set()
    for url_data in all_urls:
        if url_data['plataforma'] in filter_platforms:
            establecimientos_validos.add(url_data['id_establecimiento'])
    
    with col_f2:
        # Filtro por establecimiento con nombres (solo los que tienen URLs en plataformas seleccionadas)
        estab_options = {
            f"{establecimientos[eid]['nombre']} (ID:{eid})": eid 
            for eid in establecimientos.keys()
            if eid in establecimientos_validos  # Solo mostrar establecimientos con URLs en plataformas seleccionadas
        }
        
        # Default: todos los establecimientos válidos
        filter_establishments_display = st.multiselect(
            "🏨 Establecimientos",
            options=list(estab_options.keys()),
            default=list(estab_options.keys())
        )
        filter_establishments = [estab_options[name] for name in filter_establishments_display]
    
    with col_f3:
        # Filtro por URL específica (opcional) - solo URLs de plataformas seleccionadas
        url_options = {
            f"{u['plataforma']}-{establecimientos_dict.get(u['id_establecimiento'], 'N/A')[:20]}": u['id_plataforma_url']
            for u in all_urls
            if u['plataforma'] in filter_platforms  # Solo URLs de plataformas seleccionadas
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
    if st.button("🚀 Scrapear Pendientes", type="primary", use_container_width=True, disabled=st.session_state.scraping_in_progress):
        if len(urls_to_scrape) == 0:
            st.warning("No hay URLs pendientes")
        else:
            # Guardar filtros en session_state
            st.session_state.scraping_filters = {
                'check_in': check_in,
                'check_out': check_out,
                'platforms': filter_platforms,
                'establishments': filter_establishments,
                'establishments_dict': establecimientos_dict
            }
            st.session_state.scraping_in_progress = True
            st.session_state.scraping_results = []

with col_btn2:
    # Forzar re-scraping
    if st.button("⚡ Forzar Todas", help="Ignora caché", use_container_width=True, disabled=st.session_state.scraping_in_progress):
        if len(urls_filtered) == 0:
            st.warning("No hay URLs filtradas")
        else:
            # Guardar filtros y usar todas las URLs filtradas
            st.session_state.scraping_filters = {
                'check_in': check_in,
                'check_out': check_out,
                'platforms': filter_platforms,
                'establishments': filter_establishments,
                'establishments_dict': establecimientos_dict,
                'force_all': True
            }
            st.session_state.scraping_in_progress = True
            st.session_state.scraping_results = []

with col_btn3:
    # Detener scraping o ver selección
    if st.session_state.scraping_in_progress:
        if st.button("🛑 Detener", type="secondary", use_container_width=True):
            st.session_state.scraping_in_progress = False
            st.rerun()
    else:
        # Ver detalles de selección
        with st.expander("📋 Ver selección actual"):
            if urls_to_scrape:
                for url_data in urls_to_scrape[:10]:  # Máximo 10
                    st.caption(f"• {url_data['plataforma']} - {establecimientos_dict.get(url_data['id_establecimiento'], 'N/A')}")
                if len(urls_to_scrape) > 10:
                    st.caption(f"... y {len(urls_to_scrape) - 10} más")
            else:
                st.caption("Sin URLs pendientes")

# --- SECCIÓN DE SCRAPING EN PROGRESO Y TABLA DINÁMICA ---
if st.session_state.scraping_in_progress:
    st.markdown("---")
    st.subheader("📊 Scraping en Progreso")
    
    # Verificar que scraping_filters no sea None
    if st.session_state.scraping_filters is None:
        st.error("Error: Configuración de scraping no encontrada")
        st.session_state.scraping_in_progress = False
        st.stop()
    
    # Determinar qué URLs scrapear
    force_all = st.session_state.scraping_filters.get('force_all', False)
    urls_to_process = urls_filtered if force_all else urls_to_scrape
    scheduler = IncrementalScraperScheduler(cache_hours=0 if force_all else cache_hours, headless=headless)
    
    # Contenedores para actualización dinámica
    progress_container = st.empty()
    status_container = st.empty()
    table_container = st.empty()
    metrics_container = st.empty()
    
    try:
        total_urls = len(urls_to_process)
        success_count = 0
        error_count = 0
        fechas_resueltas = 0
        
        for idx, url_data in enumerate(urls_to_process):
            # Actualizar progreso
            progress = (idx + 1) / total_urls
            progress_container.progress(progress, text=f"Procesando {idx + 1}/{total_urls}")
            
            # Mostrar URL actual
            estab_name = establecimientos_dict.get(url_data['id_establecimiento'], 'N/A')
            status_container.info(f"⏳ Scraping incremental (3→2→1 noches): {url_data['plataforma']} - {estab_name}")
            
            # Ejecutar scraping INCREMENTAL con rango de fechas
            stats = scheduler.scrape_date_range(url_data, check_in, check_out)
            
            # Analizar resultados
            url_success = stats['success_3'] + stats['success_2'] + stats['success_1']
            url_errors = stats['occupied']
            fechas_totales = stats['total_dates']
            
            # Formatear mensaje
            if url_success > 0:
                mensaje_parts = []
                if stats['success_3'] > 0:
                    mensaje_parts.append(f"{stats['success_3']}×3 noches")
                if stats['success_2'] > 0:
                    mensaje_parts.append(f"{stats['success_2']}×2 noches")
                if stats['success_1'] > 0:
                    mensaje_parts.append(f"{stats['success_1']}×1 noche")
                mensaje = f"✓ {', '.join(mensaje_parts)} | {fechas_totales} fechas"
            else:
                mensaje = f"✗ Todas las fechas fallaron o ocupadas"
            
            # Guardar resultado
            st.session_state.scraping_results.append({
                'Establecimiento': estab_name,
                'Plataforma': url_data['plataforma'],
                'Estado': '✅ OK' if url_success > 0 else '❌ Error',
                'Noches': fechas_totales,
                'Mensaje': mensaje
            })
            
            if url_success > 0:
                success_count += 1
                fechas_resueltas += fechas_totales
            else:
                error_count += 1
            
            # Actualizar métricas
            col_m1, col_m2, col_m3, col_m4 = metrics_container.columns(4)
            col_m1.metric("✅ Éxitos", success_count)
            col_m2.metric("❌ Errores", error_count)
            col_m3.metric("📅 Fechas", fechas_resueltas)
            col_m4.metric("📊 Total", f"{idx + 1}/{total_urls}")
            
            # Actualizar tabla con resultados parciales
            df_results = pd.DataFrame(st.session_state.scraping_results)
            table_container.dataframe(df_results, use_container_width=True, hide_index=True)
            
            # Pequeña pausa para permitir actualización de UI
            time.sleep(0.1)
        
        # Cleanup
        if scheduler.orchestrator:
            scheduler.orchestrator.cleanup()
        
        # Finalizar
        progress_container.empty()
        status_container.success(f"✅ Scraping completado: {success_count} éxitos, {error_count} errores")
        
        # Botón para ver tabla de precios guardados
        if st.button("📊 Ver Precios Guardados", type="primary"):
            st.session_state.scraping_in_progress = False
            st.rerun()
        
    except Exception as e:
        status_container.error(f"❌ Error durante scraping: {e}")
        st.session_state.scraping_in_progress = False

# --- TABLA DE PRECIOS GUARDADOS (después de scraping o siempre visible) ---
if not st.session_state.scraping_in_progress:
    st.markdown("---")
    st.subheader("💾 Precios Guardados en BD")
    
    try:
        # Obtener precios del periodo y filtros actuales
        import sqlite3
        DB_PATH = Path(__file__).parent.parent / "database" / "price_monitor.db"
        conn = sqlite3.connect(str(DB_PATH))
        
        # Query para obtener precios del periodo seleccionado y filtros
        query = """
        SELECT 
            e.nombre_personalizado as Establecimiento,
            pu.plataforma as Plataforma,
            p.fecha_noche as Fecha,
            p.precio_base as Precio,
            p.esta_ocupado as Ocupado,
            p.fecha_scrape as 'Última Actualización'
        FROM Precios p
        JOIN Plataformas_URL pu ON p.id_plataforma_url = pu.id_plataforma_url
        JOIN Establecimientos e ON pu.id_establecimiento = e.id_establecimiento
        WHERE p.fecha_noche BETWEEN ? AND ?
        """
        
        params = [check_in.isoformat(), check_out.isoformat()]
        
        # Agregar filtros de plataforma
        if filter_platforms:
            placeholders = ','.join(['?' for _ in filter_platforms])
            query += f" AND pu.plataforma IN ({placeholders})"
            params.extend(filter_platforms)
        
        # Agregar filtros de establecimiento
        if filter_establishments:
            placeholders = ','.join(['?' for _ in filter_establishments])
            query += f" AND pu.id_establecimiento IN ({placeholders})"
            params.extend(filter_establishments)
        
        query += " ORDER BY p.fecha_noche, e.nombre_personalizado, pu.plataforma"
        
        df_precios = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df_precios.empty:
            # Formatear datos
            df_precios['Precio'] = df_precios['Precio'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "-")
            df_precios['Ocupado'] = df_precios['Ocupado'].map({0: '❌', 1: '✅'})
            df_precios['Fecha'] = pd.to_datetime(df_precios['Fecha']).dt.strftime('%Y-%m-%d')
            df_precios['Última Actualización'] = pd.to_datetime(df_precios['Última Actualización']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Mostrar tabla con altura fija para evitar parpadeo
            st.dataframe(df_precios, use_container_width=True, hide_index=True, height=400)
            
            # Métricas resumen
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("📊 Total Registros", len(df_precios))
            col_r2.metric("🏨 Establecimientos", df_precios['Establecimiento'].nunique())
            col_r3.metric("🏢 Plataformas", df_precios['Plataforma'].nunique())
            
            # Calcular precio promedio (solo valores numéricos)
            precios_numericos = df_precios['Precio'].str.replace('$', '').str.replace(',', '')
            precios_numericos = pd.to_numeric(precios_numericos, errors='coerce')
            precio_promedio = precios_numericos.mean()
            col_r4.metric("💰 Precio Promedio", f"${precio_promedio:.2f}" if not pd.isna(precio_promedio) else "-")
            
        else:
            st.info("No hay precios guardados para el periodo y filtros seleccionados.")
            st.caption("💡 Ejecuta un scraping para obtener datos.")
    
    except Exception as e:
        st.error(f"Error cargando precios de BD: {e}")


# Footer compacto
st.markdown("---")
st.caption("SDK V3 - Price Monitor")
