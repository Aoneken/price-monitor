# 💡 Ejemplos de Uso Avanzado

## Ejemplo 1: Agregar Múltiples Propiedades

Edita `config/competitors.json`:

```json
{
  "properties": [
    {
      "name": "Aizeder Eco Container House",
      "platforms": {
        "airbnb": "https://www.airbnb.com.ar/rooms/928978094650118177",
        "booking": "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"
      }
    },
    {
      "name": "Competidor 1 - Cabaña del Bosque",
      "platforms": {
        "airbnb": "https://www.airbnb.com.ar/rooms/XXXXXXX",
        "booking": "https://www.booking.com/hotel/ar/cabana-bosque.es.html"
      }
    },
    {
      "name": "Competidor 2 - Casa de Playa",
      "platforms": {
        "airbnb": "https://www.airbnb.com.ar/rooms/YYYYYYY",
        "booking": "https://www.booking.com/hotel/ar/casa-playa.es.html"
      }
    }
  ]
}
```

## Ejemplo 2: Script Personalizado de Scraping

Crea `custom_scraping.py`:

```python
import sys
from datetime import datetime, timedelta
from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager

# Configuración
PROPERTY_NAME = "Mi Propiedad"
AIRBNB_URL = "https://www.airbnb.com.ar/rooms/..."
BOOKING_URL = "https://www.booking.com/hotel/..."

# Fechas: próximos 30 días
start_date = datetime.now()
end_date = start_date + timedelta(days=30)

# Parámetros
NIGHTS = 2  # Reservas de 2 noches
GUESTS = 4  # 4 personas

# Ejecutar scraping
print(f"Scrapeando {PROPERTY_NAME} del {start_date.date()} al {end_date.date()}")

airbnb = AirbnbScraper()
booking = BookingScraper()
dm = DataManager()

results = []
results.extend(airbnb.scrape_date_range(AIRBNB_URL, start_date, end_date, NIGHTS, GUESTS))
results.extend(booking.scrape_date_range(BOOKING_URL, start_date, end_date, NIGHTS, GUESTS))

dm.save_results(results, PROPERTY_NAME)
print(f"✅ Completado! {len(results)} registros guardados")
```

## Ejemplo 3: Análisis de Datos con Pandas

```python
import pandas as pd
from src.data_manager import DataManager

# Cargar datos
dm = DataManager()
df = dm.load_data()

# Filtrar por propiedad
property_df = df[df['property_name'] == 'Aizeder Eco Container House']

# Análisis comparativo
comparison = property_df.pivot_table(
    values='price_usd',
    index='checkin',
    columns='platform',
    aggfunc='first'
)

# Calcular diferencia
comparison['Diferencia'] = comparison['Airbnb'] - comparison['Booking']
comparison['Más Barato'] = comparison[['Airbnb', 'Booking']].idxmin(axis=1)

print(comparison)

# Promedios
print("\nPrecio promedio por plataforma:")
print(property_df.groupby('platform')['price_usd'].mean())

# Días donde Airbnb es más barato
airbnb_cheaper = comparison[comparison['Diferencia'] < 0]
print(f"\nAirbnb es más barato en {len(airbnb_cheaper)} de {len(comparison)} fechas")
```

## Ejemplo 4: Exportar Datos Específicos

```python
from src.data_manager import DataManager
import pandas as pd

dm = DataManager()

# Exportar solo datos de una fecha específica
df = dm.load_data()
november_data = df[df['checkin'].str.startswith('2025-11')]

# Guardar en nuevo archivo
november_data.to_csv('data/november_prices.csv', index=False)
print("✅ Datos de noviembre exportados")

# O exportar a Excel con formato
with pd.ExcelWriter('data/custom_report.xlsx', engine='openpyxl') as writer:
    # Hoja por plataforma
    df[df['platform'] == 'Airbnb'].to_excel(writer, sheet_name='Airbnb', index=False)
    df[df['platform'] == 'Booking'].to_excel(writer, sheet_name='Booking', index=False)
    
    # Hoja de resumen
    summary = df.groupby(['platform', 'property_name'])['price_usd'].agg(['min', 'max', 'mean'])
    summary.to_excel(writer, sheet_name='Resumen')
```

## Ejemplo 5: Monitoreo Programado (Cron)

Crea `scheduled_scraping.py`:

```python
#!/usr/bin/env python3
"""
Script para ejecutar diariamente con cron
Ejemplo cron: 0 2 * * * cd /path/to/price-monitor && python scheduled_scraping.py
"""
import json
from datetime import datetime, timedelta
from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager

# Cargar configuración
with open('config/competitors.json', 'r') as f:
    config = json.load(f)

# Fechas: próximos 14 días
start = datetime.now()
end = start + timedelta(days=14)

# Scrapers
airbnb = AirbnbScraper()
booking = BookingScraper()
dm = DataManager()

# Procesar cada propiedad
for prop in config['properties']:
    print(f"\n⏰ Scrapeando: {prop['name']}")
    
    results = []
    
    if 'airbnb' in prop['platforms']:
        results.extend(airbnb.scrape_date_range(
            prop['platforms']['airbnb'], 
            start, end, nights=1, guests=2
        ))
    
    if 'booking' in prop['platforms']:
        results.extend(booking.scrape_date_range(
            prop['platforms']['booking'], 
            start, end, nights=1, adults=2
        ))
    
    dm.save_results(results, prop['name'])
    
print("\n✅ Scraping programado completado")
```

Agregar al crontab:
```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar todos los días a las 2 AM)
0 2 * * * cd /workspaces/price-monitor && /usr/bin/python3 scheduled_scraping.py >> logs/cron.log 2>&1
```

## Ejemplo 6: Análisis de Tendencias

```python
import pandas as pd
import plotly.express as px
from src.data_manager import DataManager

dm = DataManager()
df = dm.load_data()

# Convertir fechas
df['checkin'] = pd.to_datetime(df['checkin'])
df['weekday'] = df['checkin'].dt.day_name()

# Análisis por día de la semana
weekday_analysis = df.groupby(['platform', 'weekday'])['price_usd'].mean().reset_index()

# Gráfico
fig = px.bar(
    weekday_analysis, 
    x='weekday', 
    y='price_usd', 
    color='platform',
    barmode='group',
    title='Precio Promedio por Día de la Semana'
)
fig.show()

# ¿Cuándo es más barato?
print("\nPrecio promedio por día de la semana:")
print(weekday_analysis.pivot(index='weekday', columns='platform', values='price_usd'))
```

## Ejemplo 7: Alertas de Precio

```python
from src.data_manager import DataManager
import smtplib
from email.message import EmailMessage

def check_price_drops(threshold=100):
    """Verifica si hay caídas de precio significativas"""
    
    dm = DataManager()
    df = dm.load_data()
    
    # Obtener precios de hoy vs hace 7 días
    today = df[df['scraped_at'].str.startswith('2025-11-06')]
    week_ago = df[df['scraped_at'].str.startswith('2025-10-30')]
    
    # Comparar
    for platform in ['Airbnb', 'Booking']:
        today_avg = today[today['platform'] == platform]['price_usd'].mean()
        week_avg = week_ago[week_ago['platform'] == platform]['price_usd'].mean()
        
        drop = week_avg - today_avg
        
        if drop > threshold:
            print(f"🚨 ALERTA: {platform} bajó USD ${drop:.2f} esta semana!")
            # Aquí podrías enviar un email
            send_alert_email(platform, drop)

def send_alert_email(platform, amount):
    """Enviar email de alerta"""
    # Configurar con tus credenciales
    msg = EmailMessage()
    msg['Subject'] = f'Precio Bajo en {platform}!'
    msg['From'] = 'alerts@pricemoritor.com'
    msg['To'] = 'tu@email.com'
    msg.set_content(f'El precio bajó USD ${amount:.2f} en {platform}')
    
    # smtp.send(msg)  # Configurar servidor SMTP
    print(f"📧 Email enviado: {msg['Subject']}")

# Ejecutar
check_price_drops(threshold=50)
```

## Ejemplo 8: Comparación Multi-Propiedad

```python
import pandas as pd
import plotly.graph_objects as go
from src.data_manager import DataManager

dm = DataManager()
df = dm.load_data()

# Comparar precios promedio entre todas las propiedades
comparison = df.groupby(['property_name', 'platform'])['price_usd'].mean().reset_index()

# Crear gráfico de barras agrupadas
fig = go.Figure()

for platform in df['platform'].unique():
    platform_data = comparison[comparison['platform'] == platform]
    
    fig.add_trace(go.Bar(
        x=platform_data['property_name'],
        y=platform_data['price_usd'],
        name=platform
    ))

fig.update_layout(
    title='Comparación de Precios entre Propiedades',
    xaxis_title='Propiedad',
    yaxis_title='Precio Promedio (USD)',
    barmode='group'
)

fig.show()
```

---

**Tip**: Combina estos ejemplos para crear workflows personalizados según tus necesidades!
