# 🏔️ Price Monitor - Patagonia

Sistema de monitoreo de precios para establecimientos hoteleros en El Chaltén, Patagonia Argentina.

## 📋 Descripción

Price Monitor es una aplicación web completa que permite:
- 📊 Scraping automatizado de precios de Airbnb
- 📈 Análisis y visualización de curvas de precios
- 🗄️ Almacenamiento histórico en base de datos SQLite
- 🏠 Gestión de múltiples establecimientos y plataformas
- 📅 Organización por temporadas y workspaces

## 🚀 Inicio Rápido

### Requisitos
- Python 3.10+
- pip

### Instalación

```bash
# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Activar entorno virtual
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar aplicación web
python run_webapp.py
```

La aplicación estará disponible en: `http://127.0.0.1:8000`

## 📁 Estructura del Proyecto

```
price-monitor/
├── price_monitor/          # Core del sistema de scraping
│   ├── cli/               # CLI para ejecución manual
│   ├── core/              # Lógica de negocio (calendar, models, selection)
│   └── providers/         # Integraciones con plataformas (Airbnb)
│
├── webapp/                # Aplicación web FastAPI
│   ├── static/           # CSS y JavaScript
│   │   ├── app.js        # Lógica frontend completa
│   │   └── styles.css    # Estilos Supabase-inspired
│   ├── templates/        # Templates HTML
│   │   └── index.html    # SPA principal
│   ├── crud.py           # Operaciones de base de datos
│   ├── database.py       # Configuración SQLAlchemy
│   ├── main.py           # Endpoints FastAPI
│   ├── models.py         # Modelos SQLAlchemy
│   └── schemas.py        # Schemas Pydantic
│
├── scripts/              # Scripts de utilidad
│   ├── add_missing_listings.py      # Importar establecimientos
│   ├── scrape_real_prices.py        # Script de scraping standalone
│   └── update_platform_sources.py   # Actualizar plataformas
│
├── tests/                # Suite de tests
│   ├── unit/             # Tests unitarios
│   └── integration/      # Tests de integración
│
├── data/                 # Datos de entrada
│   └── establecimientos.csv  # Lista de establecimientos
│
├── logs/                 # Logs de la aplicación
├── htmlcov/             # Reportes de cobertura
│
├── requirements.txt      # Dependencias de producción
├── requirements-dev.txt  # Dependencias de desarrollo
├── pyproject.toml       # Configuración del proyecto
├── .flake8              # Configuración linting
└── Makefile             # Comandos de desarrollo
```

## 🎯 Características Principales

### 1. Gestión de Workspaces y Temporadas
- Organiza establecimientos por workspace (ej: "Patagonia 2025")
- Define temporadas con fechas de inicio/fin
- Asigna establecimientos a cada workspace

### 2. Multi-Plataforma
Cada establecimiento puede tener múltiples fuentes:
- ✅ **Airbnb** (soportado)
- 🔜 **Booking.com** (próximamente)
- 🔜 **Expedia** (próximamente)

### 3. Scraping Inteligente
- Selección de establecimientos por plataforma
- Configuración de fechas y número de huéspedes
- Progress tracking en tiempo real via WebSocket
- Almacenamiento automático de resultados

### 4. Analytics Avanzado
- Gráficos interactivos con Chart.js
- Curvas discontinuas cuando no hay datos
- Comparación de múltiples establecimientos
- Colores únicos por establecimiento (10 colores disponibles)
- KPIs por establecimiento y totales generales
- Filtrado por plataforma
- Exportación a CSV

### 5. Base de Datos Explorable
- Vista de todas las tablas del sistema
- Filtros avanzados por establecimiento, fechas, workspace
- **Ordenamiento dinámico** por cualquier columna (clic en headers)
- Paginación eficiente
- Vaciado de datos filtrados

## 🗄️ Modelo de Datos

### Tablas Principales

#### `workspaces`
Contenedores lógicos para organizar establecimientos.

#### `seasons`
Temporadas definidas dentro de un workspace.

#### `listings`
Establecimientos (hoteles, cabañas, etc.)
- Almacena datos básicos: nombre, ID, proveedor principal
- Relacionado con múltiples plataformas via `platform_sources`

#### `platform_sources`
Fuentes de precio por plataforma para cada listing.
- Campos: `platform` (airbnb/booking/expedia), `base_url`, `extra_data`
- `extra_data.supported` indica si la plataforma es funcional

#### `price_records`
Registros históricos de precios.
- Fecha, disponibilidad, precio por noche, total estadía
- Min/max noches, check-in/out disponibilidad

#### `scrape_jobs`
Historial de trabajos de scraping.
- Estado (pending, running, completed, failed)
- Progress tracking y current_step
- Vinculado a season y listing

## 🛠️ Desarrollo

### Comandos Make

```bash
# Formatear código
make format

# Linting
make lint

# Tests
make test
make test-unit
make test-integration
make test-coverage

# Limpiar archivos temporales
make clean

# Ver cobertura en HTML
make coverage-html
```

### Configuración de Python

El proyecto usa:
- **Black** para formateo
- **isort** para ordenar imports
- **Flake8** para linting
- **MyPy** para type checking
- **Pytest** para testing

### Tasks de VSCode

Disponibles en `.vscode/tasks.json`:
- `webapp: Start` - Inicia servidor web
- `cli: Run Scraper` - Ejecuta scraping desde CLI
- `test: All / Unit / Integration / Coverage`
- `lint: flake8 / mypy`
- `format: black / isort`

## 📊 Uso del Sistema

### 1. Configuración Inicial

1. **Crear Workspace**
   - Ir a pestaña "Configuración"
   - Crear nuevo workspace (ej: "Patagonia 2025")

2. **Agregar Establecimientos**
   - Subtab "Establecimientos"
   - Usar formulario o importar desde CSV

3. **Crear Temporada**
   - Subtab "Temporadas"
   - Definir nombre, fechas inicio/fin

### 2. Scraping de Precios

1. **Ir a pestaña "Scraping"**
2. **Seleccionar plataforma** (Airbnb por ahora)
3. **Elegir establecimientos** (solo aparecen los con soporte para plataforma seleccionada)
4. **Configurar parámetros**:
   - Fechas de inicio y fin
   - Número de huéspedes
   - Moneda
5. **Iniciar Scrape**
6. **Monitorear progreso** en tiempo real

### 3. Análisis de Datos

**Pestaña "Análisis":**
- Seleccionar fechas de análisis
- Elegir plataforma (Todas/Airbnb/Booking/Expedia)
- Marcar establecimientos a comparar
- Ver gráfico con curvas de precios
- Revisar KPIs por establecimiento
- Exportar a CSV

**Pestaña "Base de Datos":**
- Seleccionar tabla a explorar
- Aplicar filtros
- **Ordenar por cualquier columna** (clic en header)
- Exportar o vaciar datos

### 4. Historial de Jobs

**Pestaña "Jobs":**
- Ver todos los trabajos de scraping
- Estado y progreso de cada uno
- Errores y tiempos de ejecución

## 🎨 Interfaz de Usuario

Diseño compacto inspirado en **Supabase**:
- Paleta verde (`#3ecf8e` primary)
- Espaciado reducido (13px base font)
- Badges de colores para estados
- Modales y tooltips informativos
- Responsive y optimizado

## 🔧 API Endpoints

### Workspaces
- `GET /api/workspaces` - Lista de workspaces
- `POST /api/workspaces` - Crear workspace
- `PUT /api/workspaces/{id}` - Actualizar workspace

### Listings
- `GET /api/listings` - Lista de establecimientos (incluye platform_sources)
- `POST /api/listings` - Crear establecimiento
- `GET /api/prices/{listing_id}` - Precios de un establecimiento

### Scraping
- `POST /api/scrape` - Iniciar scrape individual
- `POST /api/seasons/{id}/scrape` - Scrape masivo por temporada
- `WS /ws/scrape-jobs/{job_id}` - WebSocket para progreso

### Database Explorer
- `GET /api/database/prices` - Registros de precios (paginado, filtrable, ordenable)
- `GET /api/database/listings` - Establecimientos (paginado, ordenable)
- `GET /api/database/jobs` - Jobs (paginado, filtrable, ordenable)
- `GET /api/database/seasons` - Temporadas (paginado, ordenable)
- `DELETE /api/database/{table}` - Vaciar datos filtrados

### Analytics
- `GET /api/analytics/establishments` - Datos agrupados por establecimiento

## 📝 Scripts Útiles

### Importar Establecimientos desde CSV

```bash
python scripts/add_missing_listings.py
```

### Actualizar Platform Sources

```bash
python scripts/update_platform_sources.py
```

Lee `data/establecimientos.csv` y pobla la tabla `platform_sources` con todas las URLs de cada plataforma.

### Scraping Standalone

```bash
python scripts/scrape_real_prices.py
```

## 🧪 Testing

```bash
# Todos los tests
pytest tests/ -v

# Solo unitarios
pytest tests/unit/ -v

# Con cobertura
pytest tests/ --cov=price_monitor --cov=webapp --cov-report=html

# Ver reporte de cobertura
open htmlcov/index.html
```

## 🐛 Troubleshooting

### Error: "No module named 'webapp'"
```bash
# Asegúrate de estar en el directorio raíz y con venv activado
cd /path/to/price-monitor
source .venv/bin/activate
```

### Base de datos corrupta
```bash
# Resetear base de datos
rm price_monitor.db
python -c "from webapp.database import init_db; init_db()"
```

### Puerto 8000 ocupado
```bash
# Cambiar puerto en run_webapp.py
# O matar proceso existente
lsof -ti:8000 | xargs kill -9
```

## 📦 Dependencias Principales

### Producción
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pydantic** - Validación de datos
- **Uvicorn** - ASGI server
- **Playwright** - Web scraping
- **httpx** - HTTP client

### Desarrollo
- **pytest** - Testing framework
- **black** - Code formatter
- **flake8** - Linter
- **mypy** - Type checker
- **pytest-cov** - Coverage reporting

## 🚧 Próximas Mejoras

- [ ] Soporte completo para Booking.com
- [ ] Soporte completo para Expedia
- [ ] Alertas de cambios de precio
- [ ] Dashboard de comparación de competencia
- [ ] API REST pública
- [ ] Autenticación y usuarios
- [ ] Integración con Google Sheets/Excel
- [ ] Notificaciones por email/Slack
- [ ] Despliegue en Docker

## 📄 Licencia

Proyecto interno - Uso privado

## 👤 Autor

Desarrollado para monitoreo de precios en El Chaltén, Patagonia.

---

**Última actualización:** Noviembre 2025
**Estado:** ✅ Producción - Sistema funcional completo
