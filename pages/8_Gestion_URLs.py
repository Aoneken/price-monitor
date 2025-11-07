"""
Página de Gestión de Establecimientos y URLs
Permite agregar, editar, activar/desactivar establecimientos y sus URLs
"""
import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Gestión URLs",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 Gestión de Establecimientos y URLs")
st.markdown("---")

# Conexión a BD
DB_PATH = Path(__file__).parent.parent / "database" / "price_monitor.db"

def get_db_connection():
    """Crear conexión a BD."""
    return sqlite3.connect(str(DB_PATH))

def get_establecimientos():
    """Obtener todos los establecimientos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.id_establecimiento,
            e.nombre_personalizado,
            e.fecha_creacion,
            COUNT(pu.id_plataforma_url) as total_urls,
            SUM(CASE WHEN pu.esta_activa = 1 THEN 1 ELSE 0 END) as urls_activas
        FROM Establecimientos e
        LEFT JOIN Plataformas_URL pu ON e.id_establecimiento = pu.id_establecimiento
        GROUP BY e.id_establecimiento
        ORDER BY e.nombre_personalizado
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_urls_by_establecimiento(estab_id):
    """Obtener URLs de un establecimiento."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id_plataforma_url,
            plataforma,
            url,
            esta_activa,
            created_at
        FROM Plataformas_URL
        WHERE id_establecimiento = ?
        ORDER BY plataforma
    """, (estab_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_establecimiento(nombre):
    """Agregar nuevo establecimiento."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Establecimientos (nombre_personalizado) VALUES (?)",
            (nombre,)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return True, new_id
    except Exception as e:
        conn.close()
        return False, str(e)

def update_establecimiento(estab_id, nuevo_nombre):
    """Actualizar nombre de establecimiento."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Establecimientos SET nombre_personalizado = ? WHERE id_establecimiento = ?",
            (nuevo_nombre, estab_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def delete_establecimiento(estab_id):
    """Eliminar establecimiento y sus URLs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Establecimientos WHERE id_establecimiento = ?", (estab_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def add_url(estab_id, plataforma, url):
    """Agregar URL a establecimiento."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Plataformas_URL (id_establecimiento, plataforma, url, esta_activa)
            VALUES (?, ?, ?, 1)
        """, (estab_id, plataforma, url))
        conn.commit()
        conn.close()
        return True, None
    except sqlite3.IntegrityError:
        conn.close()
        return False, "URL ya existe en la base de datos"
    except Exception as e:
        conn.close()
        return False, str(e)

def toggle_url(url_id, nueva_estado):
    """Activar/desactivar URL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Plataformas_URL SET esta_activa = ? WHERE id_plataforma_url = ?",
            (nueva_estado, url_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def delete_url(url_id):
    """Eliminar URL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Plataformas_URL WHERE id_plataforma_url = ?", (url_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

# Tabs para organizar contenido
tab1, tab2 = st.tabs(["📋 Establecimientos", "➕ Agregar Nuevo"])

with tab1:
    # Listar establecimientos
    establecimientos = get_establecimientos()
    
    if not establecimientos:
        st.info("No hay establecimientos registrados. Usa la pestaña 'Agregar Nuevo'.")
    else:
        st.markdown(f"**Total: {len(establecimientos)} establecimientos**")
        
        for estab_id, nombre, fecha_creacion, total_urls, urls_activas in establecimientos:
            with st.expander(f"🏨 **{nombre}** ({urls_activas}/{total_urls} URLs activas)", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**ID:** {estab_id} | **Creado:** {fecha_creacion[:10]}")
                
                with col2:
                    if st.button("🗑️ Eliminar", key=f"del_estab_{estab_id}", type="secondary", use_container_width=True):
                        if delete_establecimiento(estab_id):
                            st.success("Establecimiento eliminado")
                            st.rerun()
                        else:
                            st.error("Error al eliminar")
                
                # Editar nombre
                with st.form(key=f"edit_estab_{estab_id}"):
                    nuevo_nombre = st.text_input("Cambiar nombre", value=nombre)
                    if st.form_submit_button("💾 Guardar"):
                        if update_establecimiento(estab_id, nuevo_nombre):
                            st.success("Nombre actualizado")
                            st.rerun()
                        else:
                            st.error("Error al actualizar")
                
                st.markdown("---")
                st.markdown("**URLs del establecimiento:**")
                
                # Listar URLs
                urls = get_urls_by_establecimiento(estab_id)
                
                if not urls:
                    st.info("No hay URLs registradas para este establecimiento")
                else:
                    for url_id, plataforma, url, esta_activa, created_at in urls:
                        col_a, col_b, col_c, col_d = st.columns([1, 2, 4, 2])
                        
                        with col_a:
                            st.markdown(f"**{plataforma}**")
                        
                        with col_b:
                            estado = "🟢 Activa" if esta_activa else "🔴 Inactiva"
                            st.markdown(estado)
                        
                        with col_c:
                            st.markdown(f"`{url[:60]}...`")
                        
                        with col_d:
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                new_state = 0 if esta_activa else 1
                                btn_label = "⏸️" if esta_activa else "▶️"
                                if st.button(btn_label, key=f"toggle_{url_id}"):
                                    if toggle_url(url_id, new_state):
                                        st.rerun()
                            with col_btn2:
                                if st.button("🗑️", key=f"del_url_{url_id}"):
                                    if delete_url(url_id):
                                        st.rerun()
                
                # Agregar nueva URL a este establecimiento
                with st.form(key=f"add_url_{estab_id}"):
                    st.markdown("**➕ Agregar URL**")
                    col_plat, col_url = st.columns([1, 3])
                    
                    with col_plat:
                        nueva_plataforma = st.selectbox(
                            "Plataforma",
                            ["Booking", "Airbnb", "Expedia", "Vrbo"],
                            key=f"plat_{estab_id}"
                        )
                    
                    with col_url:
                        nueva_url = st.text_input("URL completa", key=f"url_{estab_id}")
                    
                    if st.form_submit_button("➕ Agregar URL"):
                        if nueva_url.strip():
                            success, error = add_url(estab_id, nueva_plataforma, nueva_url.strip())
                            if success:
                                st.success("URL agregada")
                                st.rerun()
                            else:
                                st.error(f"Error: {error}")
                        else:
                            st.warning("Ingresa una URL válida")

with tab2:
    st.header("➕ Agregar Nuevo Establecimiento")
    
    with st.form(key="new_establecimiento"):
        nombre_nuevo = st.text_input("Nombre del establecimiento", placeholder="Ej: Patagonia Eco Domes")
        
        st.markdown("**URLs iniciales (opcional):**")
        
        col1, col2 = st.columns(2)
        with col1:
            plat1 = st.selectbox("Plataforma 1", ["Ninguna", "Booking", "Airbnb", "Expedia", "Vrbo"], key="p1")
            url1 = st.text_input("URL 1", key="u1")
        
        with col2:
            plat2 = st.selectbox("Plataforma 2", ["Ninguna", "Booking", "Airbnb", "Expedia", "Vrbo"], key="p2")
            url2 = st.text_input("URL 2", key="u2")
        
        if st.form_submit_button("💾 Crear Establecimiento", type="primary"):
            if not nombre_nuevo.strip():
                st.error("El nombre es obligatorio")
            else:
                # Crear establecimiento
                success, result = add_establecimiento(nombre_nuevo.strip())
                
                if success:
                    estab_id = result
                    st.success(f"✓ Establecimiento creado (ID: {estab_id})")
                    
                    # Agregar URLs si se proporcionaron
                    urls_agregadas = 0
                    if plat1 != "Ninguna" and url1.strip():
                        if add_url(estab_id, plat1, url1.strip())[0]:
                            urls_agregadas += 1
                    
                    if plat2 != "Ninguna" and url2.strip():
                        if add_url(estab_id, plat2, url2.strip())[0]:
                            urls_agregadas += 1
                    
                    if urls_agregadas > 0:
                        st.success(f"✓ {urls_agregadas} URL(s) agregada(s)")
                    
                    st.info("Cambia a la pestaña 'Establecimientos' para ver el nuevo registro")
                else:
                    st.error(f"Error: {result}")

# Footer
st.markdown("---")
st.caption("Gestión de Establecimientos | SDK V3 - Price Monitor")
