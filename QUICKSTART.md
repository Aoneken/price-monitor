# 🚀 Quick Start Guide

## Instalación Rápida

```bash
# 1. Instalar dependencias
./install.sh

# O manualmente:
pip install -r requirements.txt
playwright install chromium
```

## Uso Básico

### Opción 1: Interfaz Web (Recomendado)

```bash
streamlit run app.py
```

Luego:
1. Abre tu navegador en `http://localhost:8501`
2. Selecciona las fechas de inicio y fin
3. Ingresa las URLs de Airbnb y Booking
4. Presiona **▶️ PLAY**
5. ¡Visualiza los resultados!

### Opción 2: Línea de Comandos

```bash
python example.py
```

## Configurar Competidores

Edita `config/competitors.json`:

```json
{
  "properties": [
    {
      "name": "Mi Propiedad",
      "platforms": {
        "airbnb": "https://www.airbnb.com.ar/rooms/...",
        "booking": "https://www.booking.com/hotel/..."
      }
    }
  ]
}
```

## Consejos

- **Rangos pequeños primero**: Empieza con 3-7 días para probar
- **Paciencia**: El scraping toma ~2 segundos por fecha
- **Datos históricos**: Se guardan automáticamente en `data/price_history.csv`
- **Exportar**: Usa el botón "Exportar a Excel" para análisis offline

## Solución de Problemas

### No se obtienen precios

Los selectores CSS pueden cambiar. Actualiza manualmente en:
- `src/airbnb_scraper.py` - línea ~62
- `src/booking_scraper.py` - línea ~61

### Error de Playwright

```bash
playwright install chromium
```

### Aplicación no inicia

```bash
cd /workspaces/price-monitor
streamlit run app.py
```

¡Listo! 🎉
