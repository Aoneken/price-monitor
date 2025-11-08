# Price Monitor

Herramienta para extraer y monitorear precios de Airbnb con histórico, caching y soporte para múltiples establecimientos.

## Instalación rápida

```bash
# Clonar y entrar al directorio
git clone https://github.com/Aoneken/price-monitor
cd price-monitor

# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Opcional: dependencias de desarrollo (pytest)
pip install -r requirements-dev.txt
```

## Uso básico

### Ejecutar para un establecimiento

```bash
# Modo simple (sin barra de progreso Rich)
.venv/bin/python -m price_monitor.cli.main \
  --start 2025-12-01 \
  --end 2025-12-15 \
  --guests 2 \
  --select "Viento" \
  --cache-hours 6 \
  --max-workers 4 \
  --output-dir output \
  --no-rich

# Modo con barra de progreso Rich (por defecto)
.venv/bin/python -m price_monitor.cli.main \
  --start 2025-12-01 \
  --end 2025-12-15 \
  --guests 2 \
  --select "Viento"
```

### Opciones principales

- `--start YYYY-MM-DD` — Fecha inicial del periodo
- `--end YYYY-MM-DD` — Fecha final del periodo
- `--guests N` — Número de huéspedes (default: 2)
- `--select SELECTOR` — Seleccionar establecimiento(s):
  - Por índice: `1` o rango `1-3`
  - Por fragmento de nombre: `Viento`, `Cerro`
- `--cache-hours HOURS` — Reutilizar datos recientes (default: 6)
- `--max-workers N` — Hilos para consultas paralelas (default: 4)
- `--output-dir PATH` — Directorio de salida (default: `output`)
- `--no-rich` — Desactivar barra de progreso (modo texto)
- `--json` — Generar JSON además de CSV
- `--freeze-before YYYY-MM-DD` — Congelar filas anteriores a fecha dada
- `--csv PATH` — Ruta al CSV de establecimientos (auto-detecta si no se especifica)

### Usar el wrapper script

```bash
.venv/bin/python scripts/scrape_real_prices.py \
  --start 2025-12-01 \
  --end 2025-12-15 \
  --select "Cerro Eléctrico" \
  --json
```

## Estructura de salida

### CSV
Cada archivo contiene:
- Metadatos en comentarios (`#`)
- Columnas: date, available, availableForCheckin, availableForCheckout, bookable, minNights, maxNights, pricePerNight, priceBasisNights, stayTotal, currency, insertedAt, notes

Ejemplo:
```csv
# Listing: Viento de Glaciares
# Listing ID: 1413234233737891700
# Period: 2025-12-01 to 2025-12-15
# Guests: 2
# Cache Hours: 6.0
#
date,available,availableForCheckin,...
2025-12-01,False,False,True,...
```

### JSON (opcional con `--json`)
Array de objetos con las mismas columnas:
```json
[
  {
    "date": "2025-12-01",
    "available": "False",
    "pricePerNight": "",
    ...
  }
]
```

## Caching y congelación

- **Cache hours**: Reutiliza filas existentes dentro de la ventana temporal especificada
- **Freeze before**: Preserva filas históricas anteriores a la fecha dada sin re-consultar
- Las filas previas a "hoy" se congelan automáticamente

## Testing

```bash
# Ejecutar todos los tests
.venv/bin/python -m pytest tests -v

# Solo tests unitarios
.venv/bin/python -m pytest tests/unit -v

# Solo tests de integración
.venv/bin/python -m pytest tests/integration -v

# Con cobertura
.venv/bin/python -m pytest tests --cov=price_monitor --cov-report=term-missing
```

## Linting

```bash
.venv/bin/python -m flake8 .
```

O usa la tarea VS Code configurada: `Tasks: Run Task > lint`

## Arquitectura

```
price_monitor/
├── core/
│   ├── calendar.py      # Fetch calendario Airbnb
│   ├── io_csv.py        # Lectura/escritura CSV con freeze
│   ├── models.py        # Modelos de datos
│   ├── rows.py          # Builder principal (caching, concurrencia)
│   └── selection.py     # Selección de establecimientos
├── providers/
│   └── airbnb.py        # GraphQL + scraping HTML precios
└── cli/
    └── main.py          # CLI unificado

scripts/
└── scrape_real_prices.py  # Wrapper conveniente

tests/
├── unit/                # Tests unitarios
└── integration/         # Tests de integración
```

## Próximos pasos (roadmap)

- [ ] Endpoint FastAPI para consulta de precios vía API REST
- [ ] Persistencia en SQLite/PostgreSQL
- [ ] Dashboard web con HTMX/Jinja2 o React
- [ ] Alertas por cambios de precio
- [ ] Soporte para Booking.com y otros providers

## Solución de problemas

### "No module named 'requests'" o similar
```bash
.venv/bin/python -m pip install -r requirements.txt
```

### Tests no se ejecutan
```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

### El CSV de establecimientos no se encuentra
Especifica la ruta explícita:
```bash
--csv tests/Foco_01/Temp-25-26/establecimientos/establecimientos.csv
```

## Licencia

MIT (pendiente)
