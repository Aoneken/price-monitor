# Price Monitor V3 🚀

Sistema completo de monitoreo de precios para propiedades en plataformas de alojamiento (Airbnb, Booking, Expedia).

## 🌟 Características

### ✅ Scraping Automatizado
- **SDK V3** con arquitectura modular (parsers + robots + normalizers)
- **Playwright** para navegación robusta y stealth
- **3 plataformas soportadas**: Airbnb, Booking, Expedia
- **Quality scoring** (0-1) basado en confiabilidad de la fuente
- **Manejo de errores** con códigos específicos por plataforma

### 📊 Interfaz Web (Streamlit)
- **Dashboard principal**: Gestión de establecimientos y URLs
- **Scraping V3**: Ejecución manual con configuración flexible
- **Monitoreo V3**: Métricas en tiempo real, actividad reciente, tendencias
- **Base de Datos**: Visualización completa de precios históricos

### 🗄️ Base de Datos
- **SQLite** con schema optimizado
- **Caché inteligente**: Evita re-scraping innecesario (configurable)
- **Histórico completo** de precios por noche
- **Tracking de errores** para diagnóstico

### 🤖 Automatización
- **Scheduler CLI**: Ejecución batch desde terminal
- **Configuración flexible**: Días adelante, noches, caché
- **Logging completo**: logs/scheduler_v3.log
- **Filtrado por plataforma**: Scrapeo selectivo

---

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/Aoneken/price-monitor.git
cd price-monitor

# Cambiar a rama v3
git checkout v3

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install chromium
```

### 2. Configurar Base de Datos

La base de datos ya existe en `database/price_monitor.db`. Si necesitas recrearla:

```bash
sqlite3 database/price_monitor.db < legacy/database/schema_completo.sql
```

### 3. Agregar URLs

Opción A - Interfaz Web:
```bash
streamlit run app.py
# Ir a página "Establecimientos" y agregar URLs
```

Opción B - Script Python:
```python
from src.persistence.database_adapter import DatabaseAdapter

adapter = DatabaseAdapter()
conn = adapter.get_connection()
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO Plataformas_URL (id_establecimiento, plataforma, url)
    VALUES (1, 'Airbnb', 'https://www.airbnb.com/rooms/12345')
""")
conn.commit()
conn.close()
```

### 4. Ejecutar Scraping

**Opción A - Interfaz Web (Recomendado):**
```bash
streamlit run app.py
# Ir a página "Scraping V3"
# Configurar parámetros y hacer clic en "Scrapear Todo"
```

**Opción B - CLI (Automatización):**
```bash
# Scrapear todas las URLs
python scheduler_v3.py

# Scrapear solo una plataforma
python scheduler_v3.py --platform Airbnb

# Configuración personalizada
python scheduler_v3.py --days-ahead 60 --nights 3 --cache-hours 48

# Ver todas las opciones
python scheduler_v3.py --help
```

**Opción C - Prueba Rápida:**
```bash
# Test con solo 1 URL para validar funcionamiento
python test_scheduler_quick.py
```

### 5. Monitorear Resultados

```bash
streamlit run app.py
# Ir a página "Monitoreo V3"
```

---

## 📁 Estructura del Proyecto

```
price-monitor/
├── src/                          # SDK V3
│   ├── parsers/                  # Extracción de datos
│   │   ├── airbnb_parser.py
│   │   ├── booking_parser.py
│   │   └── expedia_parser.py
│   ├── robots/                   # Navegación Playwright
│   │   ├── base_robot.py
│   │   ├── airbnb_robot.py
│   │   ├── booking_robot.py
│   │   └── expedia_robot.py
│   ├── normalizers/              # Normalización de datos
│   │   └── normalizer.py
│   ├── persistence/              # Integración con BD
│   │   └── database_adapter.py
│   └── orchestrator_v3.py        # Coordinador
│
├── pages/                        # Páginas Streamlit
│   ├── 6_Scraping_V3.py         # UI de scraping
│   └── 7_Monitoreo_V3.py        # Dashboard de métricas
│
├── tests_v3/                     # Tests unitarios
│   ├── test_parsers_airbnb.py
│   ├── test_parsers_booking.py
│   └── test_parsers_expedia.py
│
├── database/                     # Base de datos
│   ├── price_monitor.db         # SQLite DB
│   ├── schema.sql               # Schema mínimo
│   └── db_manager.py            # Manager legacy
│
├── logs/                         # Logs de ejecución
│   └── scheduler_v3.log
│
├── docs_v3/                      # Documentación
│   └── metodologias/            # Metodologías por plataforma
│
├── app.py                        # Aplicación principal
├── scheduler_v3.py              # Scheduler CLI
├── demo_v3.py                   # Demo del SDK
├── test_scheduler_quick.py      # Test rápido
├── requirements.txt             # Dependencias
└── README_V3.md                 # Este archivo
```

---

## 🔧 Configuración

### Parámetros del Scheduler

```bash
python scheduler_v3.py \
  --platform Airbnb \           # Plataforma específica (opcional)
  --days-ahead 30 \             # Días hacia adelante para check-in
  --nights 2 \                  # Número de noches de estadía
  --cache-hours 24 \            # Horas de caché
  --max-urls 10 \               # Límite de URLs a procesar
  --no-headless                 # Desactivar modo headless
```

### Variables de Entorno

Crear archivo `.env`:
```bash
# Base de datos
DATABASE_PATH=database/price_monitor.db

# Scraping
DEFAULT_CACHE_HOURS=24
DEFAULT_DAYS_AHEAD=30
DEFAULT_NIGHTS=2

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scheduler_v3.log
```

---

## 🧪 Testing

### Tests Unitarios (Parsers)

```bash
# Todos los tests
pytest tests_v3/ -v

# Solo Airbnb
pytest tests_v3/test_parsers_airbnb.py -v

# Con cobertura
pytest tests_v3/ --cov=src/parsers
```

### Demo del SDK (Sin navegación)

```bash
python demo_v3.py
# Seleccionar opción 1: Demo parsers
```

### Prueba Rápida (1 URL real)

```bash
python test_scheduler_quick.py
```

---

## 📊 Uso de la UI

### Scraping V3

1. **Configurar parámetros** en el sidebar:
   - Caché (horas): Evita re-scraping reciente
   - Días hacia adelante: Check-in en X días
   - Número de noches: Duración de estadía
   - Modo headless: Navegador invisible

2. **Ejecutar scraping**:
   - "Scrapear Todo": Procesa todas las URLs pendientes
   - Botones por plataforma: Scraping selectivo

3. **Ver resultados**:
   - Métricas de éxito/error
   - Progreso en tiempo real
   - Detalles de cada URL

### Monitoreo V3

**Métricas Generales:**
- Total de precios registrados
- Actividad últimas 24h
- Cobertura de URLs
- Errores recientes

**Distribución por Plataforma:**
- URLs con datos
- Total de registros
- Último scraping

**Actividad Reciente:**
- 50 últimos scrapeos
- Estado (✓ OK / ✗ Error)
- Precios encontrados
- Logs de error

**Tendencias de Precios:**
- Gráfico histórico 30 días
- Comparativa por plataforma
- Datos detallados

---

## 🔍 Contratos de Datos

### AirbnbQuote
```python
{
    'property_id': str,
    'check_in': date,
    'check_out': date,
    'nights': int,
    'currency': str,              # 'USD', 'EUR', 'ARS'
    'precio_total': float,
    'precio_por_noche': float,
    'incluye_desayuno': str,      # 'Sí' | 'No'
    'wifi_incluido': str,         # 'Sí' | 'No'
    'fuente': str,                # 'dom_breakdown'
    'quality': float,             # 0-1
    'errores': list
}
```

### BookingQuote
```python
{
    'property_id': str,
    'precio_total': float,        # base + impuestos
    'precio_por_noche': float,
    'impuestos_cargos_extra': float | None,
    # ... resto igual a Airbnb
}
```

### ExpediaQuote
```python
{
    'property_id': str,
    'precio_total_vigente': float,
    'precio_original_tachado': float | None,
    'monto_descuento': float | None,
    'porcentaje_descuento': float | None,
    # ... resto igual a Airbnb
}
```

---

## 🛠️ Solución de Problemas

### Error: "playwright not found"
```bash
playwright install chromium
```

### Error: "Database not found"
```bash
# Verificar que existe database/price_monitor.db
ls -l database/

# Si no existe, usar el schema legacy
sqlite3 database/price_monitor.db < legacy/database/schema_completo.sql
```

### Error: "No URLs activas"
```bash
# Agregar URLs desde la interfaz web o con SQL
streamlit run app.py
# Ir a "Establecimientos" → Agregar URL
```

### Scraping muy lento
```bash
# Aumentar caché para evitar re-scraping
python scheduler_v3.py --cache-hours 48

# Limitar número de URLs
python scheduler_v3.py --max-urls 5
```

### Ver logs detallados
```bash
tail -f logs/scheduler_v3.log
```

---

## 📈 Roadmap

### ✅ Completado (V3.0)
- SDK modular con parsers/robots/normalizers
- Integración completa con BD
- UI Streamlit funcional
- Scheduler CLI
- Sistema de caché
- Tests unitarios (26 tests)

### 🔄 En Progreso
- Tests de integración con fixtures HTML
- Validación con URLs reales de producción

### 📋 Planificado
- **V3.1**: Scraping concurrente (asyncio + Playwright async)
- **V3.2**: Alertas de cambios de precio (email/Telegram)
- **V3.3**: API REST sobre el orchestrator
- **V3.4**: Soporte para más plataformas (Vrbo, Hotels.com)
- **V3.5**: Machine Learning para predicción de precios

---

## 🤝 Contribución

El proyecto está en desarrollo activo. Para contribuir:

1. Fork del repositorio
2. Crear branch feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📄 Licencia

MIT License - Ver LICENSE para detalles

---

## 📞 Soporte

- **Issues**: GitHub Issues
- **Documentación**: `docs_v3/`
- **SDK Docs**: `SDK_V3_README.md`
- **Implementación**: `IMPLEMENTACION_SDK_V3_COMPLETA.md`

---

**Versión**: 3.0.0  
**Última actualización**: 2025-01-08  
**Branch**: v3  
**Status**: ✅ Producción Ready
