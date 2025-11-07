# 📂 Estructura del Proyecto - Price Monitor V3

## 📊 Vista General

```
price-monitor/
├── 📄 README.md                      # Documentación principal
├── 📄 CHANGELOG.md                   # Historial de cambios
├── 📄 requirements.txt              # Dependencias Python
├── 🐍 app.py                        # Aplicación Streamlit principal
│
├── 📁 src/                          # SDK V3 - Código fuente principal
│   ├── 🔍 parsers/                  # Extracción de datos por plataforma
│   │   ├── airbnb_parser.py
│   │   ├── booking_parser.py
│   │   └── expedia_parser.py
│   ├── 🤖 robots/                   # Navegación con Playwright
│   │   ├── base_robot.py
│   │   ├── airbnb_robot.py
│   │   ├── booking_robot.py
│   │   └── expedia_robot.py
│   ├── ✅ normalizers/              # Normalización y validación
│   │   └── normalizer.py
│   ├── 💾 persistence/              # Integración con base de datos
│   │   └── database_adapter.py
│   ├── 🔧 utils/                    # Utilidades compartidas
│   ├── 🎯 domain/                   # Modelos de dominio
│   └── 🎭 orchestrator_v3.py       # Coordinador multi-plataforma
│
├── 📁 pages/                        # Páginas Streamlit
│   ├── 6_Scraping_V3.py            # UI de scraping manual
│   ├── 7_Monitoreo_V3.py           # Dashboard de métricas
│   └── 8_Gestion_URLs.py           # CRUD de establecimientos
│
├── 📁 tests_v3/                     # Tests unitarios y de integración
│   ├── test_parsers_airbnb.py
│   ├── test_parsers_booking.py
│   ├── test_parsers_expedia.py
│   ├── test_booking_quick.py
│   ├── test_scheduler_quick.py
│   ├── test_viento_glaciares.py
│   ├── fixtures/                    # Datos de prueba HTML/JSON
│   └── README.md
│
├── 📁 scripts/                      # Scripts de automatización
│   ├── scheduler_v3.py             # Scheduler CLI principal
│   └── demo_v3.py                  # Demo del SDK
│
├── 📁 database/                     # Base de datos SQLite
│   ├── price_monitor.db            # BD principal (no versionada)
│   ├── schema.sql                  # Schema mínimo V3
│   └── db_manager.py               # Manager de BD
│
├── 📁 config/                       # Configuración de la aplicación
│   ├── __init__.py
│   └── settings.py
│
├── 📁 docs_v3/                      # Documentación técnica completa
│   ├── README.md                   # Índice de documentación
│   ├── VISION_NEGOCIO_V3.md
│   ├── RESUMEN_METODOLOGIAS_Y_TESTS.md
│   ├── SDK_V3_README.md
│   ├── FASE_0_CONSTITUCION_Y_MIGRACION.md
│   ├── FASE_1_DATOS_Y_DOMINIO.md
│   ├── FASE_2_INGESTA_Y_SCRAPING.md
│   ├── FASE_3_PERSISTENCIA_Y_NORMALIZACION.md
│   ├── FASE_4_OBSERVABILIDAD_Y_TESTING.md
│   ├── FASE_5_UI_Y_API.md
│   ├── FASE_6_SEGURIDAD_Y_OPERACION.md
│   ├── executive/                   # Documentos ejecutivos
│   │   ├── RESUMEN_FINAL_V3.txt
│   │   ├── SISTEMA_V3_COMPLETO.md
│   │   ├── MEJORAS_UX_V3.md
│   │   └── IMPLEMENTACION_SDK_V3_COMPLETA.md
│   └── metodologias/               # Metodologías por plataforma
│       ├── METODOLOGIA_AIRBNB.md
│       ├── METODOLOGIA_BOOKING.md
│       ├── METODOLOGIA_EXPEDIA.md
│       ├── RESULTADOS_EXPLORACION_AIRBNB.md
│       ├── RESULTADOS_EXPLORACION_BOOKING.md
│       └── RESULTADOS_EXPLORACION_EXPEDIA.md
│
├── 📁 research/                     # Exploraciones iniciales
│   ├── explore_airbnb.py
│   ├── explore_booking.py
│   └── explore_expedia.py
│
├── 📁 logs/                         # Logs de ejecución
│   └── scheduler_v3.log            # Log del scheduler
│
├── 📁 debug/                        # Debug y capturas HTML
│   ├── debug_booking_capture.py
│   └── *.html                      # Capturas HTML (no versionadas)
│
├── 📁 legacy/                       # Código V1/V2 (referencia histórica)
│   ├── app.py
│   ├── scrapers/
│   ├── pages/
│   ├── tests/
│   └── docs/
│
└── 📁 .vscode/                      # Configuración VS Code
    └── tasks.json                  # Tasks de desarrollo

```

## 🎯 Puntos de Entrada

### Para Usuarios
- **Inicio rápido**: `README.md`
- **Aplicación web**: `streamlit run app.py`
- **Scheduler CLI**: `python scripts/scheduler_v3.py --help`

### Para Desarrolladores
- **SDK**: `docs_v3/SDK_V3_README.md`
- **Tests**: `pytest tests_v3/ -v`
- **Demo**: `python scripts/demo_v3.py`
- **Documentación**: `docs_v3/README.md`

### Para Gestión
- **Resumen ejecutivo**: `docs_v3/executive/RESUMEN_FINAL_V3.txt`
- **Visión de negocio**: `docs_v3/VISION_NEGOCIO_V3.md`
- **Historial de cambios**: `CHANGELOG.md`

## 📚 Documentación por Audiencia

### 👤 Usuario Final
```
README.md
    ├─ Instalación y configuración
    ├─ Inicio rápido
    ├─ Flujo de trabajo
    └─ Solución de problemas
```

### 👨‍💻 Desarrollador
```
docs_v3/
    ├─ SDK_V3_README.md (Referencia API)
    ├─ FASE_1_DATOS_Y_DOMINIO.md (Modelo de datos)
    ├─ FASE_2_INGESTA_Y_SCRAPING.md (Arquitectura scraping)
    └─ metodologias/ (Detalles por plataforma)
```

### 👔 Gestión/Negocio
```
docs_v3/executive/
    ├─ RESUMEN_FINAL_V3.txt (Resumen ejecutivo)
    ├─ SISTEMA_V3_COMPLETO.md (Visión completa)
    └─ MEJORAS_UX_V3.md (Funcionalidades)
```

## 🔄 Flujo de Datos

```
1. UI/CLI → Orchestrator
2. Orchestrator → Robot (Playwright)
3. Robot → HTML capturado
4. HTML → Parser
5. Parser → Quote object (dict)
6. Quote → Normalizer
7. Normalizer → DatabaseAdapter
8. DatabaseAdapter → SQLite
9. SQLite → UI (consultas y visualización)
```

## 🧪 Testing

```
tests_v3/
├── Unit tests (parsers)         # Test de extracción sin navegación
├── Integration tests            # Test con BD y orchestrator
└── Quick tests                  # Validación rápida con URLs reales
```

Ejecutar: `pytest tests_v3/ -v`

## 📦 Dependencias Principales

- **streamlit**: Interfaz web interactiva
- **playwright**: Scraping con navegador
- **sqlite3**: Base de datos (built-in)
- **pandas**: Análisis de datos
- **plotly**: Visualizaciones
- **pytest**: Testing

Ver `requirements.txt` para lista completa.

## 🚀 Comandos Útiles

```bash
# Desarrollo
streamlit run app.py                    # Iniciar app web
python scripts/scheduler_v3.py          # Scraping CLI
python scripts/demo_v3.py               # Demo SDK

# Testing
pytest tests_v3/ -v                     # Todos los tests
pytest tests_v3/test_parsers_*.py -v    # Tests específicos
python tests_v3/test_scheduler_quick.py # Test rápido

# Utilidades
tail -f logs/scheduler_v3.log           # Ver logs en tiempo real
sqlite3 database/price_monitor.db       # Acceder a BD
```

## 🗂️ Archivos No Versionados

Estos archivos están en `.gitignore`:

```
.venv/                  # Entorno virtual
__pycache__/           # Cache Python
*.pyc                  # Bytecode
.pytest_cache/         # Cache pytest
logs/*.log             # Logs
database/*.db          # Base de datos
debug/*.html           # Capturas HTML
.env                   # Variables de entorno
```

## 📝 Convenciones

### Código
- **PEP 8**: Estilo de código Python
- **Type hints**: Anotaciones de tipo en funciones críticas
- **Docstrings**: Documentación en funciones públicas

### Commits
- `feat:` Nueva característica
- `fix:` Corrección de bug
- `docs:` Documentación
- `refactor:` Refactorización
- `test:` Tests

### Archivos
- `snake_case.py`: Archivos Python
- `UPPERCASE.md`: Documentos importantes
- `PascalCase/`: Carpetas de recursos

## 🔗 Enlaces Rápidos

- [README Principal](README.md)
- [Documentación Completa](docs_v3/README.md)
- [Changelog](CHANGELOG.md)
- [Tests](tests_v3/README.md)
- [SDK Docs](docs_v3/SDK_V3_README.md)

---

**Versión**: 3.0.0  
**Branch**: v3  
**Status**: ✅ Producción Ready  
**Última actualización**: 2025-11-07
