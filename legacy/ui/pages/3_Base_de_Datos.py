"""
Pestaña 3: Base de Datos
Visor completo de la tabla de Precios con filtros y exportación
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.db_manager import get_db

st.set_page_config(page_title="Base de Datos", page_icon="💾", layout="wide")

st.title("💾 Base de Datos de Precios")
st.markdown("Explora, filtra y exporta todos los datos recolectados.")

db = get_db()

# === SECCIÓN 1: FILTROS DE BÚSQUEDA ===
st.header("🔎 Filtros de Búsqueda")

with st.form("filtros_busqueda"):
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Filtro por Establecimientos
        establecimientos = db.get_all_establecimientos()
        nombres_est = ["Todos"] + [e['nombre_personalizado'] for e in establecimientos]
        ids_est_map = {e['nombre_personalizado']: e['id_establecimiento'] for e in establecimientos}
        
        establecimientos_seleccionados = st.multiselect(
            "Establecimientos",
            options=nombres_est,
            default=["Todos"],
            help="Selecciona uno o más establecimientos"
        )
        
        # Filtro por Plataformas
        plataformas_seleccionadas = st.multiselect(
            "Plataformas",
            options=["Todas", "Booking", "Airbnb", "Vrbo"],
            default=["Todas"],
            help="Selecciona una o más plataformas"
        )
    
    with col_f2:
        # Rango de Fecha Noche
        st.subheader("Rango de Fechas (Noche)")
        fecha_noche_inicio = st.date_input(
            "Desde",
            value=(datetime.now() - timedelta(days=30)).date(),
            key="fecha_noche_inicio"
        )
        fecha_noche_fin = st.date_input(
            "Hasta",
            value=(datetime.now() + timedelta(days=60)).date(),
            key="fecha_noche_fin"
        )
        
        # Rango de Fecha Scrape
        st.subheader("Rango de Fechas (Scrape)")
        col_scrape1, col_scrape2 = st.columns(2)
        with col_scrape1:
            usar_filtro_scrape = st.checkbox("Filtrar por fecha de scrape")
        if usar_filtro_scrape:
            with col_scrape2:
                fecha_scrape_inicio = st.date_input(
                    "Scrape Desde",
                    value=(datetime.now() - timedelta(days=7)).date(),
                    key="fecha_scrape_inicio"
                )
                fecha_scrape_fin = st.date_input(
                    "Scrape Hasta",
                    value=datetime.now().date(),
                    key="fecha_scrape_fin"
                )
        else:
            fecha_scrape_inicio = None
            fecha_scrape_fin = None
    
    # Filtro adicional
    solo_ocupados = st.checkbox("Mostrar solo registros Ocupados (Precio = $0)")
    
    buscar = st.form_submit_button("🔍 Buscar en BBDD", type="primary", use_container_width=True)

# === SECCIÓN 2: RESULTADOS ===
if buscar or 'datos_cargados' not in st.session_state:
    st.header("📊 Resultados de la Búsqueda")
    
    # Preparar filtros
    ids_establecimiento = None
    if "Todos" not in establecimientos_seleccionados:
        ids_establecimiento = [ids_est_map[nombre] for nombre in establecimientos_seleccionados if nombre in ids_est_map]
    
    plataformas = None
    if "Todas" not in plataformas_seleccionadas:
        plataformas = plataformas_seleccionadas
    
    fecha_noche_inicio_dt = datetime.combine(fecha_noche_inicio, datetime.min.time())
    fecha_noche_fin_dt = datetime.combine(fecha_noche_fin, datetime.min.time())
    
    fecha_scrape_inicio_dt = datetime.combine(fecha_scrape_inicio, datetime.min.time()) if usar_filtro_scrape and fecha_scrape_inicio else None
    fecha_scrape_fin_dt = datetime.combine(fecha_scrape_fin, datetime.min.time()) if usar_filtro_scrape and fecha_scrape_fin else None
    
    # Ejecutar consulta
    try:
        with st.spinner("Consultando base de datos..."):
            resultados = db.get_precios_by_filters(
                ids_establecimiento=ids_establecimiento,
                plataformas=plataformas,
                fecha_noche_inicio=fecha_noche_inicio_dt,
                fecha_noche_fin=fecha_noche_fin_dt,
                fecha_scrape_inicio=fecha_scrape_inicio_dt,
                fecha_scrape_fin=fecha_scrape_fin_dt,
                solo_ocupados=solo_ocupados
            )
        
        if resultados:
            # Convertir a DataFrame para mejor visualización
            df = pd.DataFrame(resultados)
            
            # Formatear columnas
            df['fecha_noche'] = pd.to_datetime(df['fecha_noche']).dt.strftime('%Y-%m-%d')
            df['fecha_scrape'] = pd.to_datetime(df['fecha_scrape']).dt.strftime('%Y-%m-%d %H:%M')
            df['precio_base'] = df['precio_base'].apply(lambda x: f"${x:.2f}" if x > 0 else "$0.00")
            df['esta_ocupado'] = df['esta_ocupado'].apply(lambda x: "✅ Sí" if x else "❌ No")
            
            # Renombrar columnas para mejor lectura
            df_display = df[[
                'establecimiento', 'plataforma', 'fecha_noche', 'precio_base',
                'esta_ocupado', 'noches_encontradas', 'fecha_scrape',
                'incluye_limpieza_base', 'incluye_impuestos_base', 'ofrece_desayuno',
                'error_log'
            ]].rename(columns={
                'establecimiento': 'Establecimiento',
                'plataforma': 'Plataforma',
                'fecha_noche': 'Fecha Noche',
                'precio_base': 'Precio Base',
                'esta_ocupado': 'Ocupado',
                'noches_encontradas': 'Noches',
                'fecha_scrape': 'Fecha Scrape',
                'incluye_limpieza_base': 'Limpieza',
                'incluye_impuestos_base': 'Impuestos',
                'ofrece_desayuno': 'Desayuno',
                'error_log': 'Error'
            })
            
            # Métricas
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Total de Registros", len(df))
            
            with col_m2:
                precios_validos = df[df['precio_base'] != "$0.00"]
                if len(precios_validos) > 0:
                    # Extraer valores numéricos
                    precios_numericos = precios_validos['precio_base'].str.replace('$', '').str.replace(',', '').astype(float)
                    precio_promedio = precios_numericos.mean()
                    st.metric("Precio Promedio", f"${precio_promedio:.2f}")
                else:
                    st.metric("Precio Promedio", "N/A")
            
            with col_m3:
                ocupados = df[df['esta_ocupado'] == "✅ Sí"]
                st.metric("Registros Ocupados", len(ocupados))
            
            with col_m4:
                # Usar df_display que tiene la columna renombrada
                con_error = df_display[df_display['Error'].notna()]
                st.metric("Con Errores", len(con_error))
            
            st.divider()
            
            # Tabla de resultados
            st.subheader("Tabla de Datos")
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            # Botón de exportación
            st.divider()
            st.subheader("📥 Exportar Datos")
            
            col_exp1, col_exp2 = st.columns([2, 1])
            
            with col_exp1:
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="Exportar a CSV",
                    data=csv,
                    file_name=f"precios_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_exp2:
                st.info(f"📊 {len(df)} registros listos para exportar")
            
            # Guardar en session_state para persistencia
            st.session_state['datos_cargados'] = True
            
        else:
            st.warning("📭 No se encontraron resultados con los filtros aplicados.")
    
    except Exception as e:
        st.error(f"❌ Error al consultar la base de datos: {e}")
        st.exception(e)

else:
    st.info("👆 Configura los filtros y haz clic en 'Buscar en BBDD' para ver los resultados.")

# === SECCIÓN 3: GESTIÓN DE DATOS (ELIMINAR) ===
st.divider()
st.header("🗑️ Gestión de Datos")

with st.expander("⚠️ Eliminar Datos de la Base de Datos", expanded=False):
    st.warning("**ATENCIÓN**: Esta acción es irreversible. Los datos eliminados no se pueden recuperar.")
    
    st.subheader("Configurar Eliminación")
    
    col_del1, col_del2 = st.columns(2)
    
    with col_del1:
        # Filtro por Establecimientos para eliminar
        establecimientos_eliminar = st.multiselect(
            "Establecimientos a eliminar",
            options=nombres_est,
            default=[],
            help="Selecciona establecimientos (dejar vacío para todos)",
            key="del_establecimientos"
        )
        
        # Filtro por Plataformas para eliminar
        plataformas_eliminar = st.multiselect(
            "Plataformas a eliminar",
            options=["Booking", "Airbnb", "Expedia", "Vrbo"],
            default=[],
            help="Selecciona plataformas (dejar vacío para todas)",
            key="del_plataformas"
        )
    
    with col_del2:
        st.subheader("Período a Eliminar")
        usar_rango_fecha = st.checkbox("Limitar por rango de fechas", value=True, key="del_usar_fecha")
        
        if usar_rango_fecha:
            fecha_del_inicio = st.date_input(
                "Desde (fecha noche)",
                value=(datetime.now() - timedelta(days=30)).date(),
                key="del_fecha_inicio"
            )
            fecha_del_fin = st.date_input(
                "Hasta (fecha noche)",
                value=datetime.now().date(),
                key="del_fecha_fin"
            )
        else:
            fecha_del_inicio = None
            fecha_del_fin = None
    
    # Vista previa de lo que se eliminará
    st.divider()
    
    if st.button("🔍 Vista Previa de Eliminación", use_container_width=True):
        try:
            # Preparar filtros
            ids_est_eliminar = None
            if establecimientos_eliminar and "Todos" not in establecimientos_eliminar:
                ids_est_eliminar = [ids_est_map[nombre] for nombre in establecimientos_eliminar if nombre in ids_est_map]
            
            plat_eliminar = plataformas_eliminar if plataformas_eliminar else None
            
            fecha_inicio_dt = datetime.combine(fecha_del_inicio, datetime.min.time()) if usar_rango_fecha and fecha_del_inicio else None
            fecha_fin_dt = datetime.combine(fecha_del_fin, datetime.min.time()) if usar_rango_fecha and fecha_del_fin else None
            
            # Contar registros
            if not any([ids_est_eliminar, plat_eliminar, fecha_inicio_dt, fecha_fin_dt]):
                st.error("⚠️ Debe especificar al menos un filtro (establecimiento, plataforma o fechas)")
            else:
                count = db.count_precios_by_filters(
                    ids_establecimiento=ids_est_eliminar,
                    plataformas=plat_eliminar,
                    fecha_noche_inicio=fecha_inicio_dt,
                    fecha_noche_fin=fecha_fin_dt
                )
                
                if count > 0:
                    st.error(f"⚠️ **{count} registros** serán eliminados con estos filtros")
                    
                    # Mostrar resumen
                    st.info(f"""
                    **Filtros aplicados:**
                    - Establecimientos: {', '.join(establecimientos_eliminar) if establecimientos_eliminar else 'Todos'}
                    - Plataformas: {', '.join(plataformas_eliminar) if plataformas_eliminar else 'Todas'}
                    - Fechas: {fecha_del_inicio if usar_rango_fecha else 'Sin límite'} a {fecha_del_fin if usar_rango_fecha else 'Sin límite'}
                    """)
                else:
                    st.success("✅ No hay registros que coincidan con estos filtros")
        
        except Exception as e:
            st.error(f"Error al contar registros: {e}")
    
    # Confirmación y eliminación
    st.divider()
    st.subheader("Confirmación de Eliminación")
    
    col_conf1, col_conf2 = st.columns([3, 1])
    
    with col_conf1:
        confirmacion = st.text_input(
            "Escribe 'ELIMINAR' para confirmar:",
            key="confirmacion_eliminar",
            help="Debes escribir exactamente 'ELIMINAR' en mayúsculas"
        )
    
    with col_conf2:
        st.write("")  # Espaciado
        st.write("")  # Espaciado
        eliminar_btn = st.button(
            "🗑️ ELIMINAR DATOS",
            type="primary",
            disabled=(confirmacion != "ELIMINAR"),
            use_container_width=True
        )
    
    if eliminar_btn and confirmacion == "ELIMINAR":
        try:
            # Preparar filtros
            ids_est_eliminar = None
            if establecimientos_eliminar and "Todos" not in establecimientos_eliminar:
                ids_est_eliminar = [ids_est_map[nombre] for nombre in establecimientos_eliminar if nombre in ids_est_map]
            
            plat_eliminar = plataformas_eliminar if plataformas_eliminar else None
            
            fecha_inicio_dt = datetime.combine(fecha_del_inicio, datetime.min.time()) if usar_rango_fecha and fecha_del_inicio else None
            fecha_fin_dt = datetime.combine(fecha_del_fin, datetime.min.time()) if usar_rango_fecha and fecha_del_fin else None
            
            # Validar filtros
            if not any([ids_est_eliminar, plat_eliminar, fecha_inicio_dt, fecha_fin_dt]):
                st.error("⚠️ Debe especificar al menos un filtro para eliminar datos")
            else:
                with st.spinner("Eliminando registros..."):
                    deleted_count = db.delete_precios_by_filters(
                        ids_establecimiento=ids_est_eliminar,
                        plataformas=plat_eliminar,
                        fecha_noche_inicio=fecha_inicio_dt,
                        fecha_noche_fin=fecha_fin_dt
                    )
                
                st.success(f"✅ Se eliminaron **{deleted_count}** registros exitosamente")
                
                # Limpiar confirmación
                st.session_state['confirmacion_eliminar'] = ""
                
                # Recomendar recargar
                st.info("💡 Haz clic en 'Buscar en BBDD' nuevamente para actualizar los resultados")
        
        except ValueError as ve:
            st.error(f"⚠️ Error de validación: {ve}")
        except Exception as e:
            st.error(f"❌ Error al eliminar datos: {e}")
            st.exception(e)

# Información adicional
with st.expander("ℹ️ Guía de Filtros"):
    st.markdown("""
    ### Tipos de Filtros:
    
    - **Establecimientos**: Filtra por una o más propiedades específicas
    - **Plataformas**: Booking, Airbnb, Vrbo, o todas
    - **Fecha Noche**: La noche específica de la estadía
    - **Fecha Scrape**: Cuándo se obtuvo el dato (útil para ver datos recientes)
    - **Solo Ocupados**: Muestra solo registros donde no había disponibilidad
    
    ### Interpretación de Columnas:
    
    - **Precio Base**: Precio por noche (0 si no disponible)
    - **Ocupado**: Si el precio es 0, se asume ocupación
    - **Noches**: Cuántas noches se buscaron para encontrar ese precio (1, 2 o 3)
    - **Detalles**: Si incluye limpieza, impuestos, desayuno
    - **Error**: Problemas técnicos durante el scraping
    """)
