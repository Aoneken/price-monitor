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
        options=list(nombres_establecimientos.keys())
    )
    id_establecimiento = nombres_establecimientos[establecimiento_seleccionado]
    
    # Verificar URLs activas
    urls_activas = db.get_urls_activas_by_establecimiento(id_establecimiento)
    st.info(f"📊 URLs activas para '{establecimiento_seleccionado}': **{len(urls_activas)}**")
    
    if urls_activas:
        for url in urls_activas:
            st.caption(f"• {url['plataforma']}")

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

if fecha_fin < fecha_inicio:
    st.error("❌ Rango de fechas inválido.")
    st.stop()

# Botón de inicio
iniciar_scraping = st.button("🚀 INICIAR MONITOREO", type="primary", use_container_width=True)

if iniciar_scraping:
    st.header("📊 Progreso del Scraping")
    
    # Contenedores para actualización en tiempo real
    contenedor_estado = st.empty()
    contenedor_progreso = st.empty()
    contenedor_tabla = st.empty()
    contenedor_log = st.empty()
    
    # Lista para acumular resultados
    resultados_tabla = []
    
    # Función callback para actualizar UI
    def callback_progreso(mensaje, progreso, resultado):
        if mensaje:
            contenedor_estado.info(f"🔄 {mensaje}")
        
        if progreso is not None:
            contenedor_progreso.progress(progreso)
        
        if resultado:
            # Agregar resultado a la tabla
            resultados_tabla.append({
                "Plataforma": resultado.plataforma,
                "Fecha": resultado.fecha_noche.strftime('%Y-%m-%d'),
                "Precio": f"${resultado.precio:.2f}" if resultado.precio > 0 else "No disponible",
                "Noches": resultado.noches if resultado.noches > 0 else "-",
                "Estado": "✅ OK" if not resultado.error else f"❌ {resultado.error[:30]}..."
            })
            
            # Actualizar tabla (mostrar últimos 20)
            contenedor_tabla.dataframe(
                resultados_tabla[-20:],
                use_container_width=True,
                hide_index=True
            )
    
    # Ejecutar scraping
    try:
        orchestrator = ScrapingOrchestrator(callback_progreso)
        
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.min.time())
        
        resultados = orchestrator.ejecutar(
            id_establecimiento,
            fecha_inicio_dt,
            fecha_fin_dt
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
