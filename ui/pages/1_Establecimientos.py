"""
Pestaña 1: Gestión de Establecimientos (CRUD)
Permite crear, ver, editar y eliminar establecimientos y sus URLs
"""
import streamlit as st
from database.db_manager import get_db
import sqlite3

st.set_page_config(page_title="Establecimientos", page_icon="🏠", layout="wide")

st.title("🏠 Gestión de Establecimientos")
st.markdown("Administra tu portafolio de propiedades y configura URLs de monitoreo.")

db = get_db()

# === SECCIÓN 1: MAESTRO (Gestionar Establecimientos) ===
st.header("📋 Portafolio de Establecimientos")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Añadir Nuevo Establecimiento")
    with st.form("form_nuevo_establecimiento"):
        nombre = st.text_input("Nombre Personalizado", placeholder="Ej: Cabaña Sol, Depto Centro")
        submitted = st.form_submit_button("➕ Añadir Establecimiento")
        
        if submitted:
            if nombre.strip():
                try:
                    id_nuevo = db.create_establecimiento(nombre.strip())
                    st.success(f"✅ Establecimiento '{nombre}' creado con ID: {id_nuevo}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al crear establecimiento: {e}")
            else:
                st.warning("⚠️ El nombre no puede estar vacío")

with col2:
    st.subheader("Estadísticas")
    establecimientos = db.get_all_establecimientos()
    st.metric("Total de Establecimientos", len(establecimientos))
    
    # Contar URLs totales
    total_urls = 0
    for est in establecimientos:
        urls = db.get_urls_by_establecimiento(est['id_establecimiento'])
        total_urls += len(urls)
    st.metric("Total de URLs", total_urls)

st.divider()

# === SECCIÓN 2: DETALLE (Gestionar Establecimiento Seleccionado) ===
st.header("🔧 Gestionar Establecimiento")

if not establecimientos:
    st.info("📭 No hay establecimientos registrados. Crea uno arriba para empezar.")
else:
    # Selector de establecimiento
    nombres_establecimientos = {
        est['nombre_personalizado']: est['id_establecimiento']
        for est in establecimientos
    }
    
    establecimiento_seleccionado = st.selectbox(
        "Seleccionar Establecimiento",
        options=list(nombres_establecimientos.keys()),
        key="selector_establecimiento"
    )
    
    if establecimiento_seleccionado:
        id_establecimiento = nombres_establecimientos[establecimiento_seleccionado]
        
        col_acciones1, col_acciones2 = st.columns([3, 1])
        
        with col_acciones1:
            st.info(f"📌 Trabajando con: **{establecimiento_seleccionado}** (ID: {id_establecimiento})")
        
        with col_acciones2:
            if st.button("🗑️ Eliminar Establecimiento", type="secondary"):
                with st.form("confirmar_eliminacion"):
                    st.warning(f"⚠️ ¿Estás seguro de eliminar '{establecimiento_seleccionado}'? Esto eliminará todas sus URLs y precios.")
                    confirmado = st.form_submit_button("Sí, Eliminar")
                    
                    if confirmado:
                        if db.delete_establecimiento(id_establecimiento):
                            st.success(f"✅ '{establecimiento_seleccionado}' eliminado correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar")
        
        st.divider()
        
        # URLs asociadas
        st.subheader(f"🌐 URLs Registradas para '{establecimiento_seleccionado}'")
        
        urls = db.get_urls_by_establecimiento(id_establecimiento)
        
        if urls:
            for url in urls:
                with st.expander(f"🔗 {url['plataforma']} - {'✅ Activa' if url['esta_activa'] else '⏸️ Pausada'}"):
                    col_url1, col_url2, col_url3 = st.columns([3, 1, 1])
                    
                    with col_url1:
                        st.text_input("URL", url['url'], disabled=True, key=f"url_{url['id_plataforma_url']}")
                        st.caption(f"Creada: {url['created_at']}")
                    
                    with col_url2:
                        nuevo_estado = st.toggle(
                            "Activa",
                            value=url['esta_activa'],
                            key=f"toggle_{url['id_plataforma_url']}"
                        )
                        if nuevo_estado != url['esta_activa']:
                            if db.toggle_url_activa(url['id_plataforma_url'], nuevo_estado):
                                st.success("✓")
                                st.rerun()
                    
                    with col_url3:
                        if st.button("🗑️ Borrar", key=f"delete_{url['id_plataforma_url']}"):
                            if db.delete_plataforma_url(url['id_plataforma_url']):
                                st.success("✓ Eliminada")
                                st.rerun()
        else:
            st.info("📭 No hay URLs registradas para este establecimiento.")
        
        st.divider()
        
        # Formulario para añadir nueva URL
        st.subheader(f"➕ Añadir Nueva URL a '{establecimiento_seleccionado}'")
        
        with st.form("form_nueva_url"):
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                plataforma = st.selectbox(
                    "Plataforma",
                    options=['Booking', 'Airbnb', 'Vrbo'],
                    help="El nombre debe coincidir con un robot implementado"
                )
            
            with col_form2:
                url_nueva = st.text_input(
                    "URL Completa",
                    placeholder="https://www.booking.com/hotel/...",
                    help="URL del anuncio en la plataforma"
                )
            
            submitted_url = st.form_submit_button("💾 Guardar URL")
            
            if submitted_url:
                if url_nueva.strip():
                    try:
                        id_nueva_url = db.create_plataforma_url(
                            id_establecimiento,
                            plataforma,
                            url_nueva.strip()
                        )
                        st.success(f"✅ URL de {plataforma} añadida correctamente (ID: {id_nueva_url})")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        if 'UNIQUE constraint failed' in str(e):
                            st.error("❌ Esta URL ya existe en la base de datos")
                        elif 'CHECK constraint failed' in str(e):
                            st.error("❌ Plataforma no soportada. Usa: Booking, Airbnb o Vrbo")
                        else:
                            st.error(f"❌ Error: {e}")
                    except Exception as e:
                        st.error(f"❌ Error al guardar URL: {e}")
                else:
                    st.warning("⚠️ La URL no puede estar vacía")
