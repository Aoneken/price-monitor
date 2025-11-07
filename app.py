import streamlit as st
from database.db_manager import get_db

st.set_page_config(page_title="Price Monitor V3", page_icon="📊", layout="centered")

st.title("Price Monitor V3 — Skeleton")
st.write("Esta es una versión mínima de la aplicación (V3) enfocada en reconstruir la arquitectura.")
st.write("Consulta la documentación en `docs_v3/` para el plan completo.")

st.header("Establecimientos (demo mínima)")

db = get_db()

with st.form("nuevo_establecimiento"):
    nombre = st.text_input("Nombre del establecimiento")
    submitted = st.form_submit_button("Agregar")
    if submitted and nombre.strip():
        eid = db.create_establecimiento(nombre.strip())
        st.success(f"Establecimiento creado con ID: {eid}")

establecimientos = db.get_all_establecimientos()
if establecimientos:
    st.subheader("Listado")
    for e in establecimientos:
        st.write(f"- {e['id_establecimiento']}: {e['nombre_personalizado']} (creado: {e['fecha_creacion']})")
else:
    st.info("Aún no hay establecimientos. Agrega uno arriba.")
