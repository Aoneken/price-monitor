"""
Pestaña 2: Scraping
Interfaz para iniciar el proceso de scraping con progreso en tiempo real
"""
import streamlit as st
from datetime import datetime, timedelta
from database.db_manager import get_db
from scrapers.orchestrator import ScrapingOrchestrator

st.set_page_config(page_title="Scraping", page_icon="🔍", layout="wide")

st.title("🔍 Monitoreo de Precios")
st.markdown("Ejecuta el scraping de precios para tus establecimientos.")

db = get_db()

# === SECCIÓN 1: CONFIGURACIÓN DE LA TAREA ===
st.header("⚙️ Configuración del Scraping")

establecimientos = db.get_all_establecimientos()

if not establecimientos:
    st.warning("⚠️ No hay establecimientos registrados. Ve a la pestaña 'Establecimientos' para crear uno.")
    st.stop()

# Selector de establecimiento
nombres_establecimientos = {
    est['nombre_personalizado']: est['id_establecimiento']
    for est in establecimientos
}

col_config1, col_config2 = st.columns(2)

with col_config1:
    establecimiento_seleccionado = st.selectbox(
        "Seleccionar Establecimiento",
        options=list(nombres_establecimientos.keys()),
        key="selector_establecimiento"
    )
    id_establecimiento = nombres_establecimientos[establecimiento_seleccionado]
    
    # Verificar URLs activas (forzar recarga desde BD, sin cache)
    urls_activas = db.get_urls_activas_by_establecimiento(id_establecimiento)
    
    # Debug: Mostrar info detallada
    with st.expander("🔍 Debug: Información de URLs", expanded=False):
        st.write(f"**ID Establecimiento:** {id_establecimiento}")
        st.write(f"**Total URLs activas:** {len(urls_activas)}")
        st.json([{
            'plataforma': url['plataforma'],
            'url_truncada': url['url'][:60] + '...',
            'esta_activa': bool(url['esta_activa'])
        } for url in urls_activas])
    
    st.info(f"📊 URLs activas para '{establecimiento_seleccionado}': **{len(urls_activas)}**")
    
    # 🆕 SELECTOR DE PLATAFORMAS
    st.subheader("Plataformas a Scrapear")
    
    plataformas_disponibles = sorted(list(set([url['plataforma'] for url in urls_activas])))
    
    if len(plataformas_disponibles) > 1:
        plataformas_seleccionadas = st.multiselect(
            "Seleccionar Plataforma(s)",
            options=plataformas_disponibles,
            default=plataformas_disponibles,  # Por defecto todas
            help="Puedes seleccionar una o más plataformas para scrapear",
            key="selector_plataformas"
        )
    elif len(plataformas_disponibles) == 1:
        # Si solo hay una plataforma, no mostrar selector
        plataformas_seleccionadas = plataformas_disponibles
        st.info(f"Única plataforma disponible: **{plataformas_disponibles[0]}**")
    else:
        plataformas_seleccionadas = []
        st.error("⚠️ No hay plataformas activas para este establecimiento")
    
    # Filtrar URLs según plataformas seleccionadas
    if plataformas_seleccionadas:
        urls_a_scrapear = [url for url in urls_activas if url['plataforma'] in plataformas_seleccionadas]
        st.success(f"✅ {len(urls_a_scrapear)} URL(s) seleccionada(s) para scraping")
        for url in urls_a_scrapear:
            st.caption(f"• {url['plataforma']}")
    else:
        urls_a_scrapear = []
        st.warning("⚠️ No has seleccionado ninguna plataforma")

with col_config2:
    # Selector de rango de fechas
    st.subheader("Rango de Fechas")
    
    fecha_inicio = st.date_input(
        "Fecha de Inicio",
        value=datetime.now().date(),
        help="Primera noche a monitorear"
    )
    
    fecha_fin = st.date_input(
        "Fecha de Fin",
        value=(datetime.now() + timedelta(days=30)).date(),
        help="Última noche a monitorear"
    )
    
    # Calcular días
    if fecha_fin >= fecha_inicio:
        dias_total = (fecha_fin - fecha_inicio).days + 1
        st.metric("Días a Scrapear", dias_total)
    else:
        st.error("❌ La fecha de fin debe ser posterior a la fecha de inicio")

st.divider()

# === SECCIÓN 2: EJECUCIÓN Y PROGRESO ===
if not urls_activas:
    st.error("❌ No hay URLs activas para este establecimiento. Agrega URLs en la pestaña 'Establecimientos'.")
    st.stop()

if not plataformas_seleccionadas or not urls_a_scrapear:
    st.warning("⚠️ Debes seleccionar al menos una plataforma para iniciar el scraping.")
    st.stop()

if fecha_fin < fecha_inicio:
    st.error("❌ Rango de fechas inválido.")
    st.stop()

# Botón de inicio
iniciar_scraping = st.button("🚀 INICIAR MONITOREO", type="primary", use_container_width=True)

if iniciar_scraping:
    st.header("📊 Progreso del Scraping en Tiempo Real")
    
    # Contenedores para actualización en tiempo real
    col_estado1, col_estado2 = st.columns([2, 1])
    with col_estado1:
        contenedor_estado = st.empty()
    with col_estado2:
        contenedor_stats = st.empty()
    
    contenedor_progreso = st.empty()
    contenedor_detalles = st.empty()
    contenedor_tabla = st.empty()
    contenedor_log = st.empty()
    
    # Lista para acumular resultados
    resultados_tabla = []
    estadisticas = {
        'exitosos': 0,
        'no_disponibles': 0,
        'errores': 0,
        'total': 0,
        'url_actual': '',
        'plataforma_actual': '',
        'fecha_actual': '',
        'intento_noches': 0
    }
    
    # Función callback para actualizar UI
    def callback_progreso(mensaje, progreso, resultado):
        # Actualizar mensaje principal
        if mensaje:
            # Extraer información del mensaje para mostrar detalles
            if "Procesando" in mensaje:
                estadisticas['url_actual'] = mensaje
                contenedor_estado.info(f"🔄 {mensaje}")
            elif "[" in mensaje and "]" in mensaje:
                # Mensajes con formato [Plataforma] Fecha
                partes = mensaje.split("]")
                if len(partes) >= 2:
                    estadisticas['plataforma_actual'] = partes[0].replace("[", "").strip()
                    estadisticas['fecha_actual'] = partes[1].strip().split("(")[0].strip()
                    
                    # Extraer número de noches si está disponible
                    if "noche" in mensaje.lower():
                        import re
                        match = re.search(r'(\d+)\s*noche', mensaje.lower())
                        if match:
                            estadisticas['intento_noches'] = int(match.group(1))
                    
                contenedor_estado.info(f"🔄 {mensaje}")
            else:
                contenedor_estado.info(f"🔄 {mensaje}")
        
        # Actualizar barra de progreso
        if progreso is not None:
            porcentaje = int(progreso * 100)
            contenedor_progreso.progress(progreso, text=f"Progreso: {porcentaje}%")
        
        # Mostrar detalles de la instancia actual
        if estadisticas['plataforma_actual'] or estadisticas['fecha_actual']:
            with contenedor_detalles.container():
                col_det1, col_det2, col_det3 = st.columns(3)
                with col_det1:
                    st.metric("🌐 Plataforma Actual", estadisticas['plataforma_actual'] or "-")
                with col_det2:
                    st.metric("📅 Fecha Procesando", estadisticas['fecha_actual'] or "-")
                with col_det3:
                    noches_text = f"{estadisticas['intento_noches']} noche(s)" if estadisticas['intento_noches'] > 0 else "-"
                    st.metric("🏨 Buscando", noches_text)
        
        # Procesar resultado
        if resultado:
            estadisticas['total'] += 1
            
            # Clasificar resultado
            if resultado.error and "No disponible" not in resultado.error:
                estadisticas['errores'] += 1
                estado_emoji = "❌"
                estado_texto = f"Error: {resultado.error[:30]}..."
            elif resultado.precio > 0:
                estadisticas['exitosos'] += 1
                estado_emoji = "✅"
                estado_texto = "Precio encontrado"
            else:
                estadisticas['no_disponibles'] += 1
                estado_emoji = "🚫"
                estado_texto = "No disponible"
            
            # Agregar resultado a la tabla
            resultados_tabla.append({
                "Estado": estado_emoji,
                "Plataforma": resultado.plataforma,
                "Fecha": resultado.fecha_noche.strftime('%Y-%m-%d'),
                "Precio": f"${resultado.precio:.2f}" if resultado.precio > 0 else "-",
                "Noches": resultado.noches if resultado.noches > 0 else "-",
                "Detalle": estado_texto,
                "Hora": resultado.timestamp.strftime('%H:%M:%S')
            })
            
            # Actualizar estadísticas en tiempo real
            with contenedor_stats.container():
                st.metric(
                    "Progreso",
                    f"{estadisticas['total']} procesados",
                    delta=f"✅ {estadisticas['exitosos']} | 🚫 {estadisticas['no_disponibles']} | ❌ {estadisticas['errores']}"
                )
            
            # Actualizar tabla (mostrar últimos 15)
            contenedor_tabla.dataframe(
                resultados_tabla[-15:],
                use_container_width=True,
                hide_index=True
            )
    
    # Ejecutar scraping
    try:
        orchestrator = ScrapingOrchestrator(callback_progreso)
        
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.min.time())
        
        # 🆕 PASAR PLATAFORMAS SELECCIONADAS AL ORCHESTRATOR
        resultados = orchestrator.ejecutar(
            id_establecimiento,
            fecha_inicio_dt,
            fecha_fin_dt,
            plataformas_filtro=plataformas_seleccionadas  # <-- Nuevo parámetro
        )
        
        # Mostrar resumen final
        contenedor_estado.success("✅ Scraping completado exitosamente!")
        contenedor_progreso.progress(1.0)
        
        st.divider()
        st.header("📈 Resumen de Resultados")
        
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            st.metric("Total Procesados", len(resultados))
        
        with col_res2:
            exitosos = sum(1 for r in resultados if r.precio > 0)
            st.metric("Precios Encontrados", exitosos)
        
        with col_res3:
            no_disponibles = sum(1 for r in resultados if r.precio == 0 and not r.error)
            st.metric("No Disponibles", no_disponibles)
        
        with col_res4:
            con_error = sum(1 for r in resultados if r.error)
            st.metric("Errores", con_error)
        
        # Tabla completa de resultados
        if resultados_tabla:
            st.subheader("Tabla Completa de Resultados")
            st.dataframe(resultados_tabla, use_container_width=True, hide_index=True)
            
            # Botón de descarga
            import pandas as pd
            df = pd.DataFrame(resultados_tabla)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Resultados (CSV)",
                data=csv,
                file_name=f"scraping_{establecimiento_seleccionado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        contenedor_estado.error(f"❌ Error durante el scraping: {e}")
        st.exception(e)

else:
    st.info("👆 Configura los parámetros y haz clic en 'INICIAR MONITOREO' para comenzar.")
    
    # Mostrar información útil
    with st.expander("ℹ️ Cómo funciona el scraping"):
        st.markdown("""
        ### Proceso de Scraping:
        
        1. **Lógica de 48h**: Solo se actualizarán datos con más de 48 horas de antigüedad
        2. **Búsqueda Inteligente**: Intenta 3, 2, y 1 noche(s) hasta encontrar disponibilidad
        3. **Rate Limiting**: Esperas aleatorias (3-8s) entre peticiones para evitar bloqueos
        4. **Retry Logic**: Si falla, reintenta hasta 3 veces con exponential backoff
        5. **Anti-Detección**: Navegador configurado con modo stealth
        
        ### Interpretación de Resultados:
        
        - **Precio > $0**: Disponible al precio mostrado
        - **Precio = $0 (No disponible)**: No hay disponibilidad (ocupado)
        - **Error**: Problema técnico (CAPTCHA, timeout, etc.)
        """)
