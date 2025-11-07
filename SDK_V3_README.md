# SDK V3 - Price Monitor

## Arquitectura

El SDK V3 está diseñado con separación de responsabilidades:

```
src/
├── normalizers/       # Normalización y validación de datos
│   └── normalizer.py  # PriceNormalizer, DateNormalizer, AmenityNormalizer, PriceValidator
├── parsers/           # Extracción de datos desde HTML
│   ├── airbnb_parser.py
│   ├── booking_parser.py
│   └── expedia_parser.py
├── robots/            # Navegación con Playwright
│   ├── base_robot.py
│   ├── airbnb_robot.py
│   ├── booking_robot.py
│   └── expedia_robot.py
└── orchestrator_v3.py # Coordinación multi-plataforma
```

## Características

### Normalizers
- **PriceNormalizer**: Parsing de precios con soporte multi-divisa (USD, EUR, ARS), manejo de formatos EU/US (1.200,50 vs 1,200.50)
- **DateNormalizer**: Validación de noches vs fechas check-in/check-out
- **PriceValidator**: Validación de rangos (10-10000 por noche), cálculo de descuentos
- **AmenityNormalizer**: Detección de WiFi/Desayuno, manejo de elementos `<del>` (tachados)

### Parsers
Cada parser implementa la metodología específica de su plataforma:

#### AirbnbParser
- Extrae precio total del breakdown DOM
- Detecta noches del texto ("por X noches")
- Maneja precios tachados (descuentos)
- Quality score: 0.95 para DOM, 0.8 para fallbacks

#### BookingParser
- Extrae precio base + impuestos separados
- Patrón específico: "US$XXX" o "€XXX"
- Detecta "WiFi gratis" exacto
- Suma impuestos al total final

#### ExpediaParser
- Extrae precio vigente + tachado
- Detecta badge de descuento ("$XX de dto.")
- Calcula porcentaje de descuento
- Valida coherencia precio original > vigente

### Robots
Navegación automatizada con Playwright:

- **BaseRobot**: Clase abstracta con configuración stealth
- **AirbnbRobotV3**: Abre breakdown de precios, espera panel sticky
- **BookingRobotV3**: Selecciona habitación, extrae resumen
- **ExpediaRobotV3**: Scroll a sticky card, extrae precios y descuentos

### Orchestrator
Coordina múltiples robots:

```python
orchestrator = OrchestratorV3(headless=True)

results = orchestrator.scrape_establishment(
    platform='airbnb',
    url='https://...',
    check_in=date(2025, 2, 1),
    check_out=date(2025, 2, 3),
    property_id='airbnb_12345'
)

orchestrator.cleanup()
```

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install chromium
```

## Uso

### 1. Demo de Parsers (sin navegación)
```bash
python demo_v3.py
# Seleccionar opción 1
```

### 2. Scraping en vivo
```python
from datetime import date, timedelta
from src.orchestrator_v3 import OrchestratorV3

# Inicializar
orchestrator = OrchestratorV3(headless=True)

# Scraping de una plataforma
result = orchestrator.scrape_establishment(
    platform='airbnb',  # o 'booking', 'expedia'
    url='https://www.airbnb.com/rooms/12345',
    check_in=date.today() + timedelta(days=30),
    check_out=date.today() + timedelta(days=32),
    property_id='airbnb_12345'
)

print(f"Status: {result['status']}")
if result['status'] == 'success':
    quote = result['data']
    print(f"Precio total: {quote['precio_total']}")
    print(f"Precio por noche: {quote['precio_por_noche']}")
    print(f"WiFi: {quote['wifi_incluido']}")
    print(f"Desayuno: {quote['incluye_desayuno']}")

# Limpieza
orchestrator.cleanup()
```

### 3. Scraping multi-plataforma
```python
establishments = [
    {
        'platform': 'airbnb',
        'url': 'https://...',
        'check_in': date(2025, 2, 1),
        'check_out': date(2025, 2, 3),
        'property_id': 'airbnb_001'
    },
    {
        'platform': 'booking',
        'url': 'https://...',
        'check_in': date(2025, 2, 1),
        'check_out': date(2025, 2, 3),
        'property_id': 'booking_002'
    }
]

results = orchestrator.scrape_all(establishments)

for result in results:
    print(f"{result['platform']}: {result['status']}")
```

## Contratos de Datos

### AirbnbQuote
```python
{
    'property_id': str,
    'check_in': date,
    'check_out': date,
    'nights': int,
    'currency': str,  # 'USD', 'EUR', 'ARS'
    'precio_total': float,
    'precio_por_noche': float,
    'incluye_desayuno': str,  # 'Sí' | 'No'
    'wifi_incluido': str,     # 'Sí' | 'No'
    'fuente': str,
    'quality': float,  # 0-1
    'errores': list
}
```

### BookingQuote
```python
{
    'property_id': str,
    'check_in': date,
    'check_out': date,
    'nights': int,
    'currency': str,
    'precio_total': float,  # base + impuestos
    'precio_por_noche': float,
    'incluye_desayuno': str,
    'wifi_incluido': str,
    'impuestos_cargos_extra': Optional[float],
    'fuente': str,
    'quality': float,
    'errores': list
}
```

### ExpediaQuote
```python
{
    'property_id': str,
    'check_in': date,
    'check_out': date,
    'nights': int,
    'currency': str,
    'precio_total_vigente': float,
    'precio_por_noche': float,
    'incluye_desayuno': str,
    'wifi_incluido': str,
    'precio_original_tachado': Optional[float],
    'monto_descuento': Optional[float],
    'porcentaje_descuento': Optional[float],
    'fuente': str,
    'quality': float,
    'errores': list
}
```

## Tests

```bash
# Ejecutar suite completa
pytest tests_v3/ -v

# Ejecutar tests de una plataforma específica
pytest tests_v3/test_parsers_airbnb.py -v
pytest tests_v3/test_parsers_booking.py -v
pytest tests_v3/test_parsers_expedia.py -v
```

**Cobertura actual**: 26 tests unitarios, 100% passing

## Manejo de Errores

El SDK define códigos de error específicos:

### Errores Comunes
- `PRICE_NOT_FOUND`: No se encontró precio en el HTML
- `NIGHTS_NOT_FOUND`: No se pudo determinar número de noches
- `PRICE_OUT_OF_RANGE`: Precio fuera del rango válido (10-10000)

### Errores Airbnb
- `NIGHTS_MISMATCH`: Noches en HTML ≠ (check_out - check_in).days

### Errores Booking
- `BOOKING_PRICE_NOT_FOUND`: No se encontró precio base
- `BOOKING_TAX_AMBIGUOUS`: Formato de impuestos inesperado

### Errores Expedia
- `EXPEDIA_PRICE_NOT_FOUND`: No se encontró precio vigente
- `EXPEDIA_DISCOUNT_AMBIGUOUS`: Precio original ≤ vigente (inválido)

## Calidad de Datos

Cada quote incluye un `quality` score (0-1):

- **0.95**: Extracción desde DOM breakdown (máxima confiabilidad)
- **0.90**: Descuentos presentes (puede haber ambigüedad)
- **0.80**: Fallback a métodos alternativos
- **<0.80**: Múltiples fallbacks o datos incompletos

## Roadmap

- [ ] Soporte para más divisas (GBP, JPY, BRL)
- [ ] Detección de tarifas no reembolsables
- [ ] Extracción de políticas de cancelación
- [ ] Caché de resultados de scraping
- [ ] Modo batch con concurrencia
- [ ] Integración con base de datos (SQLite/Postgres)
- [ ] API REST sobre el orchestrator

## Licencia

MIT
