"""
Página de Monitoreo V3
Visualiza el estado actual de los datos scrapeados
"""
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.persistence.database_adapter import DatabaseAdapter


st.set_page_config(
    page_title="Monitoreo V3",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Monitoreo de Datos V3")

# Control manual de actualización
col_title, col_refresh = st.columns([4, 1])
with col_refresh:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")


@st.cache_data(ttl=60)
def get_scraping_stats():
    """Obtiene estadísticas de scraping."""
    adapter = DatabaseAdapter()
    conn = adapter.get_connection()
    
    # Total de precios registrados
    total_prices = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM Precios",
        conn
    ).iloc[0]['total']
    
    # Precios de últimas 24h
    recent_prices = pd.read_sql_query(
        """
        SELECT COUNT(*) as total 
        FROM Precios 
        WHERE fecha_scrape >= datetime('now', '-24 hours')
        """,
        conn
    ).iloc[0]['total']
    
    # URLs con datos
    urls_with_data = pd.read_sql_query(
        """
        SELECT COUNT(DISTINCT id_plataforma_url) as total 
        FROM Precios
        """,
        conn
    ).iloc[0]['total']
    
    # URLs activas
    total_urls = pd.read_sql_query(
        """
        SELECT COUNT(*) as total 
        FROM Plataformas_URL 
        WHERE esta_activa = TRUE
        """,
        conn
    ).iloc[0]['total']
    
    # Errores recientes
    errors_24h = pd.read_sql_query(
        """
        SELECT COUNT(*) as total 
        FROM Precios 
        WHERE error_log IS NOT NULL 
        AND fecha_scrape >= datetime('now', '-24 hours')
        """,
        conn
    ).iloc[0]['total']
    
    conn.close()
    
    return {
        'total_prices': total_prices,
        'recent_prices': recent_prices,
        'urls_with_data': urls_with_data,
        'total_urls': total_urls,
        'errors_24h': errors_24h
    }


@st.cache_data(ttl=60)
def get_platform_distribution():
    """Distribución de precios por plataforma."""
    adapter = DatabaseAdapter()
    conn = adapter.get_connection()
    
    df = pd.read_sql_query(
        """
        SELECT 
            p.plataforma,
            COUNT(DISTINCT pr.id_plataforma_url) as urls_con_datos,
            COUNT(*) as total_registros,
            MAX(pr.fecha_scrape) as ultimo_scrape
        FROM Plataformas_URL p
        LEFT JOIN Precios pr ON p.id_plataforma_url = pr.id_plataforma_url
        WHERE p.esta_activa = TRUE
        GROUP BY p.plataforma
        ORDER BY total_registros DESC
        """,
        conn
    )
    
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_recent_activity():
    """Actividad reciente de scraping."""
    adapter = DatabaseAdapter()
    conn = adapter.get_connection()
    
    df = pd.read_sql_query(
        """
        SELECT 
            p.plataforma,
            p.url,
            pr.fecha_scrape,
            pr.precio_base,
            pr.noches_encontradas,
            pr.error_log
        FROM Precios pr
        JOIN Plataformas_URL p ON pr.id_plataforma_url = p.id_plataforma_url
        WHERE pr.fecha_scrape >= datetime('now', '-24 hours')
        ORDER BY pr.fecha_scrape DESC
        LIMIT 50
        """,
        conn
    )
    
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_price_trends():
    """Tendencias de precios."""
    adapter = DatabaseAdapter()
    conn = adapter.get_connection()
    
    df = pd.read_sql_query(
        """
        SELECT 
            DATE(fecha_scrape) as fecha,
            plataforma,
            AVG(precio_base) as precio_promedio,
            COUNT(*) as num_registros
        FROM Precios pr
        JOIN Plataformas_URL p ON pr.id_plataforma_url = p.id_plataforma_url
        WHERE fecha_scrape >= datetime('now', '-30 days')
        AND precio_base > 0
        GROUP BY DATE(fecha_scrape), plataforma
        ORDER BY fecha DESC, plataforma
        """,
        conn
    )
    
    conn.close()
    return df


# Métricas principales
st.header("📈 Métricas Generales")

stats = get_scraping_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Precios", f"{stats['total_prices']:,}")

with col2:
    st.metric("Últimas 24h", f"{stats['recent_prices']:,}")

with col3:
    st.metric("URLs con Datos", f"{stats['urls_with_data']}/{stats['total_urls']}")

with col4:
    coverage = (stats['urls_with_data'] / stats['total_urls'] * 100) if stats['total_urls'] > 0 else 0
    st.metric("Cobertura", f"{coverage:.1f}%")

with col5:
    st.metric("Errores 24h", stats['errors_24h'])

st.markdown("---")

# Distribución por plataforma
st.header("🌐 Distribución por Plataforma")

platform_df = get_platform_distribution()

if not platform_df.empty:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(
            platform_df,
            hide_index=True,
            use_container_width=True,
            height=200,  # Altura fija para evitar parpadeo
            column_config={
                "plataforma": "Plataforma",
                "urls_con_datos": "URLs con Datos",
                "total_registros": "Total Registros",
                "ultimo_scrape": st.column_config.DatetimeColumn(
                    "Último Scrape",
                    format="DD/MM/YYYY HH:mm"
                )
            }
        )
    
    with col2:
        st.bar_chart(
            platform_df.set_index('plataforma')['total_registros'],
            use_container_width=True
        )
else:
    st.info("No hay datos disponibles")

st.markdown("---")

# Actividad reciente
st.header("⏱️ Actividad Reciente (24h)")

activity_df = get_recent_activity()

if not activity_df.empty:
    # Agregar indicador de estado
    activity_df['estado'] = activity_df.apply(
        lambda row: '✗ Error' if pd.notna(row['error_log']) else '✓ OK',
        axis=1
    )
    
    # Acortar URLs
    activity_df['url_corta'] = activity_df['url'].apply(
        lambda x: x[:50] + '...' if len(x) > 50 else x
    )
    
    # Usar height fijo para evitar parpadeo
    st.dataframe(
        activity_df[['estado', 'plataforma', 'url_corta', 'fecha_scrape', 'precio_base', 'noches_encontradas']],
        hide_index=True,
        use_container_width=True,
        height=400,  # Altura fija
        column_config={
            "estado": "Estado",
            "plataforma": "Plataforma",
            "url_corta": "URL",
            "fecha_scrape": st.column_config.DatetimeColumn(
                "Fecha Scrape",
                format="DD/MM/YYYY HH:mm"
            ),
            "precio_base": st.column_config.NumberColumn(
                "Precio",
                format="$%.2f"
            ),
            "noches_encontradas": "Noches"
        }
    )
    
    # Errores
    errors = activity_df[activity_df['error_log'].notna()]
    if not errors.empty:
        with st.expander(f"⚠️ Ver errores ({len(errors)})"):
            for _, row in errors.iterrows():
                st.error(f"**{row['plataforma']}** - {row['url'][:50]}...")
                st.caption(f"Error: {row['error_log']}")
else:
    st.info("No hay actividad en las últimas 24 horas")

st.markdown("---")

# Tendencias de precios
st.header("📉 Tendencias de Precios (30 días)")

trends_df = get_price_trends()

if not trends_df.empty:
    # Pivot para graficar
    pivot_df = trends_df.pivot_table(
        index='fecha',
        columns='plataforma',
        values='precio_promedio',
        aggfunc='mean'
    )
    
    st.line_chart(pivot_df, use_container_width=True)
    
    # Tabla de detalle
    with st.expander("Ver datos detallados"):
        st.dataframe(
            trends_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "fecha": "Fecha",
                "plataforma": "Plataforma",
                "precio_promedio": st.column_config.NumberColumn(
                    "Precio Promedio",
                    format="$%.2f"
                ),
                "num_registros": "Registros"
            }
        )
else:
    st.info("No hay datos de tendencias disponibles")

# Footer
st.markdown("---")

st.caption("💡 SDK V3 - Price Monitor | Datos cacheados por 60 segundos. Usa el botón 'Actualizar' para refrescar.")

