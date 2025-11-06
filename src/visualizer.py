"""
Módulo de visualización de datos
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd


class PriceVisualizer:
    def __init__(self):
        self.colors = {
            'Airbnb': '#FF5A5F',
            'Booking': '#003580',
        }
    
    def create_price_comparison_chart(self, df, property_name=''):
        """
        Crea un gráfico de líneas comparando precios entre plataformas
        
        Args:
            df: DataFrame con los datos (debe tener columnas: checkin, platform, price_usd)
            property_name: nombre de la propiedad para el título
            
        Returns:
            figura de Plotly
        """
        if df is None or df.empty:
            return None
        
        # Filtrar datos válidos
        df = df[df['price_usd'].notna()].copy()
        
        # Convertir checkin a datetime
        df['checkin'] = pd.to_datetime(df['checkin'])
        
        # Ordenar por fecha
        df = df.sort_values('checkin')
        
        fig = go.Figure()
        
        # Agregar una línea por cada plataforma
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            fig.add_trace(go.Scatter(
                x=platform_data['checkin'],
                y=platform_data['price_usd'],
                mode='lines+markers',
                name=platform,
                line=dict(color=self.colors.get(platform, None), width=2),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Fecha: %{x|%Y-%m-%d}<br>' +
                             'Precio: USD $%{y:,.2f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title=f'Comparación de Precios - {property_name}',
            xaxis_title='Fecha de Check-in',
            yaxis_title='Precio (USD)',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            margin=dict(l=40, r=20, t=40, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_price_difference_chart(self, df, property_name=''):
        """
        Crea un gráfico mostrando la diferencia de precios entre plataformas
        
        Args:
            df: DataFrame con los datos
            property_name: nombre de la propiedad
            
        Returns:
            figura de Plotly
        """
        if df is None or df.empty:
            return None
        
        # Filtrar datos válidos
        df = df[df['price_usd'].notna()].copy()
        df['checkin'] = pd.to_datetime(df['checkin'])
        
        # Pivot para tener una columna por plataforma
        pivot = df.pivot_table(
            values='price_usd',
            index='checkin',
            columns='platform',
            aggfunc='first'
        )
        
        if 'Airbnb' in pivot.columns and 'Booking' in pivot.columns:
            pivot['Diferencia'] = pivot['Airbnb'] - pivot['Booking']
            pivot = pivot.dropna(subset=['Diferencia'])
            
            # Colores: verde si Airbnb es más barato, rojo si es más caro
            colors = ['green' if x < 0 else 'red' for x in pivot['Diferencia']]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=pivot.index,
                y=pivot['Diferencia'],
                marker_color=colors,
                hovertemplate='Fecha: %{x|%Y-%m-%d}<br>' +
                             'Diferencia: USD $%{y:,.2f}<br>' +
                             '<extra></extra>',
                showlegend=False
            ))
            
            # Línea en cero
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig.update_layout(
                title=f'Diferencia de Precios (Airbnb - Booking) - {property_name}',
                xaxis_title='Fecha de Check-in',
                yaxis_title='Diferencia de Precio (USD)',
                template='plotly_white',
                height=350,
                margin=dict(l=40, r=20, t=60, b=40),
                annotations=[
                    dict(
                        text="Verde: Airbnb más barato | Rojo: Airbnb más caro",
                        xref="paper", yref="paper",
                        x=0.5, y=1.05, showarrow=False,
                        font=dict(size=10)
                    )
                ]
            )
            
            return fig
        
        return None
    
    def create_summary_table(self, stats_df):
        """
        Crea una tabla con estadísticas resumidas
        
        Args:
            stats_df: DataFrame con estadísticas
            
        Returns:
            figura de Plotly con tabla
        """
        if stats_df is None or stats_df.empty:
            return None
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Plataforma'] + list(stats_df.columns),
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[stats_df.index] + [stats_df[col] for col in stats_df.columns],
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title='Estadísticas de Precios por Plataforma',
            height=200,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
    
    def create_price_distribution(self, df, property_name=''):
        """
        Crea un histograma/boxplot de distribución de precios
        
        Args:
            df: DataFrame con los datos
            property_name: nombre de la propiedad
            
        Returns:
            figura de Plotly
        """
        if df is None or df.empty:
            return None
        
        df = df[df['price_usd'].notna()].copy()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Distribución de Precios', 'Box Plot por Plataforma'),
            specs=[[{'type': 'histogram'}, {'type': 'box'}]]
        )
        
        # Histograma por plataforma
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            fig.add_trace(
                go.Histogram(
                    x=platform_data['price_usd'],
                    name=platform,
                    marker_color=self.colors.get(platform, None),
                    opacity=0.7
                ),
                row=1, col=1
            )
        
        # Box plot
        for platform in df['platform'].unique():
            platform_data = df[df['platform'] == platform]
            
            fig.add_trace(
                go.Box(
                    y=platform_data['price_usd'],
                    name=platform,
                    marker_color=self.colors.get(platform, None)
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title_text=f'Análisis de Distribución de Precios - {property_name}',
            height=350,
            margin=dict(l=40, r=20, t=40, b=40),
            showlegend=True,
            template='plotly_white'
        )
        
        fig.update_xaxes(title_text="Precio (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Frecuencia", row=1, col=1)
        fig.update_yaxes(title_text="Precio (USD)", row=1, col=2)
        
        return fig
