# 🏗️ Arquitectura del Sistema

## Visión General

El **Price Monitor** es un sistema modular de scraping y análisis de precios diseñado para ser escalable y fácil de mantener.

## Componentes Principales

### 1. **Scrapers** (`src/`)

#### `airbnb_scraper.py`
- **Responsabilidad**: Extraer precios de Airbnb
- **Método principal**: `scrape_date_range()`
- **Tecnología**: Playwright (navegador headless)
- **Rate limiting**: 2 segundos entre requests

**Flujo**:
1. Extrae el room ID de la URL
2. Construye URL con parámetros de fecha
3. Navega con Playwright
4. Busca el precio usando múltiples selectores CSS
5. Retorna datos estructurados

#### `booking_scraper.py`
- **Responsabilidad**: Extraer precios de Booking.com
- **Estructura similar** a Airbnb scraper
- **Diferencias**: Selectores CSS específicos de Booking

### 2. **Data Manager** (`src/data_manager.py`)

**Responsabilidades**:
- Guardar/cargar datos en CSV
- Filtrar datos por propiedad
- Generar estadísticas
- Exportar a Excel

**Estructura de datos**:
```python
{
    'platform': 'Airbnb' | 'Booking',
    'checkin': 'YYYY-MM-DD',
    'checkout': 'YYYY-MM-DD',
    'price_usd': float,
    'guests': int,
    'scraped_at': ISO timestamp,
    'url': str,
    'property_name': str
}
```

### 3. **Visualizer** (`src/visualizer.py`)

**Gráficos generados**:
1. **Comparación de precios**: Líneas de tiempo por plataforma
2. **Diferencia de precios**: Barras (verde = Airbnb más barato, rojo = más caro)
3. **Distribución**: Histogramas y box plots
4. **Tabla de estadísticas**: Min, Max, Promedio, Mediana

**Tecnología**: Plotly (gráficos interactivos)

### 4. **App Web** (`app.py`)

**Framework**: Streamlit

**Modos de operación**:
- 🔍 **Nuevo Scraping**: Interfaz para iniciar scraping
- 📊 **Datos Históricos**: Visualizar datos almacenados

**Features**:
- Selector de fechas
- Configuración de huéspedes/noches
- Progreso en tiempo real
- Visualizaciones interactivas
- Exportación a Excel

## Flujo de Datos

```
Usuario → Streamlit UI → Scraper → Data Manager → CSV
                              ↓
                        Visualizer → Plotly Charts
```

## Escalabilidad

### Agregar nuevas plataformas:

1. Crear `src/nueva_plataforma_scraper.py`
2. Implementar clase con métodos:
   - `scrape_price()`
   - `scrape_date_range()`
3. Agregar a `app.py`
4. Actualizar `config/competitors.json`

### Agregar nuevas visualizaciones:

1. Agregar método en `src/visualizer.py`
2. Llamar desde `app.py` en sección de históricos

### Cambiar almacenamiento:

1. Modificar `src/data_manager.py`
2. Mantener la misma interfaz (API)
3. Por ejemplo: CSV → SQLite → PostgreSQL

## Configuración

### `config/competitors.json`

Estructura para agregar propiedades:

```json
{
  "properties": [
    {
      "name": "Nombre Único",
      "platforms": {
        "airbnb": "URL completa",
        "booking": "URL completa",
        "nueva_plataforma": "URL completa"
      }
    }
  ]
}
```

## Tecnologías Utilizadas

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Web Scraping | Playwright | 1.40.0 |
| UI | Streamlit | 1.29.0 |
| Datos | Pandas | 2.1.4 |
| Visualización | Plotly | 5.18.0 |
| Parsing HTML | BeautifulSoup4 | 4.12.2 |

## Consideraciones de Diseño

### ✅ Buenas Prácticas Implementadas

1. **Separación de responsabilidades**: Cada módulo tiene una función clara
2. **Código reutilizable**: Scrapers con estructura similar
3. **Rate limiting**: Para no saturar servidores
4. **Manejo de errores**: Try/except en puntos críticos
5. **Múltiples selectores CSS**: Fallback si cambia la estructura de la página
6. **Datos estructurados**: Formato consistente para todos los datos

### ⚠️ Limitaciones Conocidas

1. **Selectores CSS frágiles**: Pueden cambiar si las páginas se actualizan
2. **Performance**: Scraping secuencial (no paralelo)
3. **Sin autenticación**: Solo funciona con páginas públicas
4. **Almacenamiento local**: CSV no es ideal para grandes volúmenes

### 🔮 Mejoras Futuras

1. **Scraping asíncrono**: Usar async/await para paralelizar
2. **Cache inteligente**: No re-scrapear datos recientes
3. **API REST**: Exponer funcionalidad vía API
4. **Base de datos real**: PostgreSQL o MongoDB
5. **Machine Learning**: Predicción de precios
6. **Alertas**: Notificaciones cuando precios bajan
7. **Autenticación**: Para páginas que requieren login

## Debugging

### Ver logs de Playwright:

```python
browser = p.chromium.launch(headless=False)  # Ver el navegador
```

### Inspeccionar selectores:

1. Abrir la página manualmente
2. F12 → Inspeccionar elemento
3. Copiar selector CSS
4. Actualizar en el scraper

### Verificar datos:

```bash
# Ver CSV
cat data/price_history.csv

# O con pandas
python -c "import pandas as pd; print(pd.read_csv('data/price_history.csv'))"
```

## Testing

```bash
# Ejecutar tests
python tests/test_basic.py

# Test manual de scraping
python example.py
```

---

**Última actualización**: Noviembre 2025
