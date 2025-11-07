"""
Pestaña 4: Dashboard
Visualización de datos agregados con gráficos y KPIs
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.db_manager import get_db

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard de Inteligencia de Precios")
st.markdown("Visualiza tendencias, patrones y obtén insights de tus datos.")

db = get_db()

# === SECCIÓN 1: FILTROS DEL DASHBOARD ===
st.header("⚙️ Configuración del Dashboard")

establecimientos = db.get_all_establecimientos()

if not establecimientos:
    st.warning("⚠️ No hay establecimientos registrados.")
    st.stop()

col_dash1, col_dash2 = st.columns(2)

with col_dash1:
    # Selector de establecimiento (solo uno para claridad)
    nombres_est = {e['nombre_personalizado']: e['id_establecimiento'] for e in establecimientos}
    establecimiento_seleccionado = st.selectbox(
        "Seleccionar Establecimiento",
        options=list(nombres_est.keys())
    )
    id_establecimiento = nombres_est[establecimiento_seleccionado]

with col_dash2:
    # Periodo de análisis
    st.subheader("Periodo de Análisis")
    periodo_inicio = st.date_input(
        "Desde",
        value=(datetime.now() - timedelta(days=30)).date()
    )
    periodo_fin = st.date_input(
        "Hasta",
        value=(datetime.now() + timedelta(days=30)).date()
    )

col_dash3, col_dash4 = st.columns(2)

with col_dash3:
    # Métrica principal
    metrica_principal = st.radio(
        "Métrica Principal",
        options=["Precio", "Ocupación"],
        horizontal=True
    )

with col_dash4:
    # Comparar plataformas
    comparar_plataformas = st.checkbox(
        "Comparar Plataformas",
        value=True,
        help="Si está marcado, muestra una línea por plataforma; si no, muestra el promedio"
    )

st.divider()

# === SECCIÓN 2: KPIs ===
st.header("📈 Indicadores Clave (KPIs)")

# Obtener estadísticas
periodo_inicio_dt = datetime.combine(periodo_inicio, datetime.min.time())
periodo_fin_dt = datetime.combine(periodo_fin, datetime.min.time())

estadisticas = db.get_estadisticas_establecimiento(
    id_establecimiento,
    periodo_inicio_dt,
    periodo_fin_dt
)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric(
        "💰 Precio Promedio",
        f"${estadisticas['precio_promedio']:.2f}",
        help="Precio promedio por noche (excluye noches sin disponibilidad)"
    )

with col_kpi2:
    st.metric(
        "🏨 Tasa de Ocupación",
        f"{estadisticas['tasa_ocupacion']:.1f}%",
        help="Porcentaje de noches sin disponibilidad (ocupadas)"
    )

with col_kpi3:
    st.metric(
        "📊 Total Registros",
        estadisticas['total_registros'],
        help="Cantidad total de puntos de datos en el periodo"
    )

with col_kpi4:
    if estadisticas['ultimo_scrape']:
        ultimo_scrape = datetime.fromisoformat(estadisticas['ultimo_scrape'])
        hace = datetime.now() - ultimo_scrape
        
        if hace.days > 0:
            tiempo_texto = f"Hace {hace.days} día(s)"
        elif hace.seconds > 3600:
            tiempo_texto = f"Hace {hace.seconds // 3600} hora(s)"
        else:
            tiempo_texto = f"Hace {hace.seconds // 60} min(s)"
        
        st.metric(
            "🕐 Último Scrape",
            tiempo_texto,
            help=f"Última actualización: {ultimo_scrape.strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        st.metric("🕐 Último Scrape", "N/A")

st.divider()

# === SECCIÓN 3: GRÁFICOS ===
st.header("📈 Visualizaciones")

# Obtener datos para gráficos
datos = db.get_precios_by_filters(
    ids_establecimiento=[id_establecimiento],
    fecha_noche_inicio=periodo_inicio_dt,
    fecha_noche_fin=periodo_fin_dt
)

if not datos:
    st.warning("📭 No hay datos para el periodo seleccionado.")
    st.stop()

# Convertir a DataFrame
df = pd.DataFrame(datos)
df['fecha_noche'] = pd.to_datetime(df['fecha_noche'])

# GRÁFICO 1: Evolución de Precios o Ocupación
if metrica_principal == "Precio":
    st.subheader("💰 Evolución de Precios por Noche")
    
    # Filtrar precios > 0
    df_precio = df[df['precio_base'] > 0].copy()
    
    if len(df_precio) == 0:
        st.warning("No hay datos de precios disponibles para el periodo.")
    else:
        if comparar_plataformas:
            # Agrupar por fecha y plataforma
            df_grouped = df_precio.groupby(['fecha_noche', 'plataforma'])['precio_base'].mean().reset_index()
            
            fig = px.line(
                df_grouped,
                x='fecha_noche',
                y='precio_base',
                color='plataforma',
                title=f"Precio Promedio por Noche - {establecimiento_seleccionado}",
                labels={
                    'fecha_noche': 'Fecha',
                    'precio_base': 'Precio (USD)',
                    'plataforma': 'Plataforma'
                },
                markers=True
            )
        else:
            # Promedio de todas las plataformas
            df_grouped = df_precio.groupby('fecha_noche')['precio_base'].mean().reset_index()
            
            fig = px.line(
                df_grouped,
                x='fecha_noche',
                y='precio_base',
                title=f"Precio Promedio por Noche (Todas las Plataformas) - {establecimiento_seleccionado}",
                labels={
                    'fecha_noche': 'Fecha',
                    'precio_base': 'Precio (USD)'
                },
                markers=True
            )
        
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Precio por Noche (USD)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

else:  # Ocupación
    st.subheader("🏨 Evolución de Ocupación")
    
    if comparar_plataformas:
        # Agrupar por fecha y plataforma
        df_grouped = df.groupby(['fecha_noche', 'plataforma'])['esta_ocupado'].apply(
            lambda x: (x.sum() / len(x)) * 100
        ).reset_index()
        df_grouped.rename(columns={'esta_ocupado': 'tasa_ocupacion'}, inplace=True)
        
        fig = px.line(
            df_grouped,
            x='fecha_noche',
            y='tasa_ocupacion',
            color='plataforma',
            title=f"Tasa de Ocupación por Día - {establecimiento_seleccionado}",
            labels={
                'fecha_noche': 'Fecha',
                'tasa_ocupacion': 'Ocupación (%)',
                'plataforma': 'Plataforma'
            },
            markers=True
        )
    else:
        # Promedio de todas las plataformas
        df_grouped = df.groupby('fecha_noche')['esta_ocupado'].apply(
            lambda x: (x.sum() / len(x)) * 100
        ).reset_index()
        df_grouped.rename(columns={'esta_ocupado': 'tasa_ocupacion'}, inplace=True)
        
        fig = px.line(
            df_grouped,
            x='fecha_noche',
            y='tasa_ocupacion',
            title=f"Tasa de Ocupación por Día (Todas las Plataformas) - {establecimiento_seleccionado}",
            labels={
                'fecha_noche': 'Fecha',
                'tasa_ocupacion': 'Ocupación (%)'
            },
            markers=True
        )
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Tasa de Ocupación (%)",
        yaxis_range=[0, 100],
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# GRÁFICO 2: Distribución de Precios por Plataforma
st.subheader("📦 Distribución de Precios por Plataforma")

df_precio = df[df['precio_base'] > 0].copy()

if len(df_precio) > 0:
    fig2 = px.box(
        df_precio,
        x='plataforma',
        y='precio_base',
        color='plataforma',
        title="Distribución de Precios (Box Plot)",
        labels={
            'plataforma': 'Plataforma',
            'precio_base': 'Precio (USD)'
        }
    )
    
    fig2.update_layout(
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No hay datos de precios disponibles.")

st.divider()

# GRÁFICO 3: Estadísticas por Plataforma
st.subheader("📊 Comparación de Plataformas")

# Calcular estadísticas por plataforma
stats_plataforma = df.groupby('plataforma').agg({
    'precio_base': lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0,
    'esta_ocupado': lambda x: (x.sum() / len(x)) * 100,
    'id_plataforma_url': 'count'
}).reset_index()

stats_plataforma.columns = ['Plataforma', 'Precio Promedio', 'Tasa Ocupación (%)', 'Total Registros']
stats_plataforma['Precio Promedio'] = stats_plataforma['Precio Promedio'].round(2)
stats_plataforma['Tasa Ocupación (%)'] = stats_plataforma['Tasa Ocupación (%)'].round(1)

st.dataframe(
    stats_plataforma,
    use_container_width=True,
    hide_index=True
)

# Gráfico de barras comparativo
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    fig3 = px.bar(
        stats_plataforma,
        x='Plataforma',
        y='Precio Promedio',
        color='Plataforma',
        title="Precio Promedio por Plataforma"
    )
    fig3.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig3, use_container_width=True)

with col_graf2:
    fig4 = px.bar(
        stats_plataforma,
        x='Plataforma',
        y='Tasa Ocupación (%)',
        color='Plataforma',
        title="Tasa de Ocupación por Plataforma"
    )
    fig4.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig4, use_container_width=True)

# Información adicional
with st.expander("ℹ️ Guía de Interpretación"):
    st.markdown("""
    ### Cómo Interpretar el Dashboard:
    
    **Precio Promedio**: Solo considera noches con disponibilidad (precio > $0)
    
    **Tasa de Ocupación**: Porcentaje de noches donde no había disponibilidad (asumiendo ocupación)
    
    **Comparar Plataformas**:
    - ✅ Activado: Muestra una línea/barra por cada plataforma
    - ❌ Desactivado: Muestra el promedio de todas las plataformas
    
    **Box Plot**: Muestra la distribución de precios:
    - Caja: Rango intercuartil (25%-75%)
    - Línea central: Mediana
    - Bigotes: Valores mínimo/máximo (sin outliers)
    - Puntos: Outliers (valores atípicos)
    """)
