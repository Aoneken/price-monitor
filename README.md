# 📊 Price Monitor V3# 📊 Price Monitor V3



> Sistema completo de monitoreo de precios para propiedades en plataformas de alojamiento (Airbnb, Booking, Expedia).> **⚠️ IMPORTANTE**: Este proyecto está en la rama `v3` con implementación completa del SDK V3.  

> Para documentación completa, ver **[README_V3.md](README_V3.md)**

[![Versión](https://img.shields.io/badge/versión-3.0.0-blue.svg)](https://github.com/Aoneken/price-monitor)

[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)## 🚀 Inicio Rápido

[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

```bash

---# Instalar dependencias

pip install -r requirements.txt

## ✨ Características Principalesplaywright install chromium



### 🤖 Scraping Inteligente# Iniciar aplicación

- **SDK V3** con arquitectura modular (parsers + robots + normalizers)streamlit run app.py

- **Playwright** para navegación robusta con modo stealth

- **3 plataformas**: Airbnb, Booking, Expedia# Ejecutar scraping automático

- **Quality scoring** (0-1) basado en confiabilidad de la fuentepython scheduler_v3.py --help

- **Manejo de errores** con códigos específicos por plataforma```



### 📊 Interfaz Web (Streamlit)---

- **Dashboard principal**: Gestión de establecimientos y URLs

- **Scraping V3**: Ejecución manual con configuración flexible## ✨ Novedades V3

- **Monitoreo V3**: Métricas en tiempo real, actividad reciente, tendencias

- **Gestión de URLs**: Crear, editar, activar/desactivar URLs por establecimiento### SDK Completo

- ✅ **Parsers modulares** por plataforma (Airbnb, Booking, Expedia)

### 🗄️ Base de Datos- ✅ **Robots con Playwright** y configuración stealth

- **SQLite** con schema optimizado e índices- ✅ **Normalizers** para datos multi-divisa y validación

- **Sistema de caché inteligente**: Evita re-scraping innecesario (configurable, default 24h)- ✅ **Orchestrator** para coordinación multi-plataforma

- **Histórico completo**: Precios por noche con timestamps- ✅ **Quality scoring** (0-1) por confiabilidad de fuente

- **Tracking de errores**: Para diagnóstico y monitoreo de calidad

### Aplicación Web

### ⚙️ Automatización- ✅ **Scraping V3**: UI para scraping manual con configuración flexible

- **Scheduler CLI**: Ejecución batch desde terminal con logging completo- ✅ **Monitoreo V3**: Dashboard con métricas en tiempo real

- **Configuración flexible**: Días adelante, noches, caché, plataformas- ✅ **Sistema de caché**: Evita re-scraping innecesario (24h default)

- **Filtrado inteligente**: Por plataforma, establecimiento o URLs específicas- ✅ **Logging completo**: logs/scheduler_v3.log

- **Logs estructurados**: `logs/scheduler_v3.log` con rotación

### Automatización

---- ✅ **Scheduler CLI**: Ejecución batch desde terminal

- ✅ **Integración con BD**: Mapeo automático a schema legacy

## 🚀 Inicio Rápido- ✅ **Filtrado por plataforma**: Scraping selectivo

- ✅ **Tests unitarios**: 26 tests, 100% passing

### 1. Instalación

---

```bash

# Clonar repositorio## 📁 Documentación

git clone https://github.com/Aoneken/price-monitor.git

cd price-monitor### Para Usuarios

- **[README_V3.md](README_V3.md)**: Guía completa de uso

# Cambiar a rama v3- **[SDK_V3_README.md](SDK_V3_README.md)**: Documentación del SDK

git checkout v3

### Para Desarrolladores

# Crear entorno virtual- **[IMPLEMENTACION_SDK_V3_COMPLETA.md](IMPLEMENTACION_SDK_V3_COMPLETA.md)**: Resumen técnico

python3 -m venv .venv- **docs_v3/metodologias/**: Metodologías por plataforma

source .venv/bin/activate  # Linux/Mac- **tests_v3/**: Suite de tests unitarios

# .venv\Scripts\activate   # Windows

---

# Instalar dependencias

pip install -r requirements.txt## 🎯 Estado del Proyecto



# Instalar navegadores de Playwright**Versión**: 3.0.0  

playwright install chromium**Branch**: v3  

```**Status**: ✅ **Producción Ready**



### 2. Iniciar la Aplicación### Completado

- [x] SDK V3 con parsers, robots, normalizers

```bash- [x] Integración completa con base de datos

streamlit run app.py- [x] UI Streamlit funcional (Scraping + Monitoreo)

```- [x] Scheduler CLI con logging

- [x] Sistema de caché inteligente

La aplicación estará disponible en `http://localhost:8501`- [x] Tests unitarios (26 tests, 100% passing)



### 3. Flujo de Trabajo### En Progreso

- [ ] Tests de integración con fixtures HTML

1. **Gestión de URLs** (Página 8)- [ ] Validación con URLs reales de producción

   - Crear establecimientos

   - Agregar URLs de Airbnb, Booking, Expedia### Roadmap

   - Activar/desactivar URLs según necesidad- [ ] Scraping concurrente (asyncio)

- [ ] Alertas de cambios de precio

2. **Scraping V3** (Página 6)- [ ] API REST

   - Configurar parámetros (check-in, noches, caché)- [ ] Soporte para más plataformas

   - Filtrar por plataforma y establecimiento

   - Ejecutar scraping manual con progreso en tiempo real---



3. **Monitoreo V3** (Página 7)## 🏗️ Arquitectura V3

   - Ver métricas generales (total precios, cobertura, errores)

   - Analizar distribución por plataforma```

   - Revisar actividad reciente y tendenciassrc/

├── parsers/          # Extracción de datos HTML

### 4. Automatización CLI├── robots/           # Navegación Playwright

├── normalizers/      # Normalización y validación

```bash├── persistence/      # Integración con BD

# Scrapear todas las URLs activas└── orchestrator_v3   # Coordinador multi-plataforma

python scripts/scheduler_v3.py```



# Solo una plataforma específica**Flujo de Datos**:

python scripts/scheduler_v3.py --platform Airbnb```

URL + Fechas → Robot (Playwright) → HTML → Parser → Normalizer → Quote → BD

# Configuración personalizada```

python scripts/scheduler_v3.py --days-ahead 60 --nights 3 --cache-hours 48

---

# Ver todas las opciones

python scripts/scheduler_v3.py --help## 📊 Características Principales (V3)

```

### 🤖 Scraping Inteligente

---- **3 plataformas**: Airbnb, Booking, Expedia

- **Playwright**: Navegación robusta y stealth

## 📁 Estructura del Proyecto- **Quality scoring**: Confiabilidad 0-1 por fuente

- **Manejo de errores**: Códigos específicos por plataforma

```

price-monitor/### 📈 Monitoreo en Tiempo Real

├── src/                          # SDK V3- **Métricas generales**: Total precios, actividad 24h, cobertura

│   ├── parsers/                  # Extracción de datos por plataforma- **Distribución**: URLs con datos por plataforma

│   │   ├── airbnb_parser.py- **Actividad reciente**: 50 últimos scrapeos con estado

│   │   ├── booking_parser.py- **Tendencias**: Gráficos históricos 30 días

│   │   └── expedia_parser.py

│   ├── robots/                   # Navegación con Playwright### 🗄️ Base de Datos

│   │   ├── base_robot.py- **SQLite** optimizado con índices

│   │   ├── airbnb_robot.py- **Caché inteligente**: Configurable (default 24h)

│   │   ├── booking_robot.py- **Histórico completo**: Precios por noche

│   │   └── expedia_robot.py- **Tracking de errores**: Para diagnóstico

│   ├── normalizers/              # Normalización y validación

│   │   └── normalizer.py---

│   ├── persistence/              # Integración con BD

│   │   └── database_adapter.py## 🚀 Uso Rápido

│   ├── utils/                    # Utilidades compartidas

│   └── orchestrator_v3.py        # Coordinador multi-plataforma### Interfaz Web

│```bash

├── pages/                        # Páginas Streamlitstreamlit run app.py

│   ├── 6_Scraping_V3.py         # UI de scraping manual```

│   ├── 7_Monitoreo_V3.py        # Dashboard de métricasIr a:

│   └── 8_Gestion_URLs.py        # CRUD de establecimientos y URLs- **"Scraping V3"**: Ejecutar scraping manual

│- **"Monitoreo V3"**: Ver métricas y tendencias

├── tests_v3/                     # Tests unitarios y de integración

│   ├── test_parsers_airbnb.py### CLI (Automatización)

│   ├── test_parsers_booking.py```bash

│   ├── test_parsers_expedia.py# Scrapear todas las URLs

│   ├── test_booking_quick.pypython scheduler_v3.py

│   ├── test_scheduler_quick.py

│   └── test_viento_glaciares.py# Solo una plataforma

│python scheduler_v3.py --platform Airbnb

├── scripts/                      # Scripts de automatización

│   ├── scheduler_v3.py          # Scheduler CLI principal# Configuración personalizada

│   └── demo_v3.py               # Demo del SDKpython scheduler_v3.py --days-ahead 60 --nights 3 --cache-hours 48

│```

├── database/                     # Base de datos SQLite

│   ├── price_monitor.db         # BD principal### Tests

│   ├── schema.sql               # Schema actualizado```bash

│   └── db_manager.py            # Manager de BD# Tests unitarios

│pytest tests_v3/ -v

├── docs_v3/                      # Documentación técnica

│   ├── executive/               # Documentos ejecutivos# Demo SDK (sin navegación)

│   │   ├── RESUMEN_FINAL_V3.txtpython demo_v3.py

│   │   ├── SISTEMA_V3_COMPLETO.md

│   │   ├── MEJORAS_UX_V3.md# Test rápido (1 URL real)

│   │   └── IMPLEMENTACION_SDK_V3_COMPLETA.mdpython test_scheduler_quick.py

│   ├── metodologias/            # Metodologías por plataforma```

│   ├── SDK_V3_README.md         # Documentación del SDK

│   └── FASE_*.md                # Documentación por fases---

│

├── logs/                         # Logs de ejecución## 📦 Estructura del Proyecto

│   └── scheduler_v3.log

│```

├── debug/                        # Debug y capturas HTMLprice-monitor/

│   └── debug_booking_capture.py├── src/                    # SDK V3

││   ├── parsers/           # Airbnb, Booking, Expedia

├── research/                     # Exploraciones iniciales│   ├── robots/            # Navegación Playwright

│   ├── explore_airbnb.py│   ├── normalizers/       # Normalización de datos

│   ├── explore_booking.py│   ├── persistence/       # Integración BD

│   └── explore_expedia.py│   └── orchestrator_v3.py

│├── pages/                  # UI Streamlit

├── legacy/                       # Código V1/V2 (referencia)│   ├── 6_Scraping_V3.py

││   └── 7_Monitoreo_V3.py

├── app.py                        # Aplicación principal Streamlit├── tests_v3/              # Tests unitarios

├── requirements.txt             # Dependencias Python├── database/              # SQLite DB

└── README.md                    # Este archivo├── docs_v3/               # Documentación

```├── logs/                  # Logs de ejecución

├── scheduler_v3.py        # CLI scheduler

---├── demo_v3.py            # Demo del SDK

└── app.py                # App principal

## 🔧 Configuración```



### Parámetros del Scheduler---



```bash## 🔧 Tecnologías

python scripts/scheduler_v3.py \

  --platform Airbnb \           # Filtrar por plataforma (opcional)- **Python 3.12+**

  --days-ahead 30 \             # Días hacia adelante para check-in- **Streamlit 1.29**: Interfaz web

  --nights 2 \                  # Número de noches de estadía- **Playwright 1.48**: Scraping con navegador

  --cache-hours 24 \            # Horas de caché (evitar re-scraping)- **SQLite**: Base de datos

  --max-urls 10 \               # Límite de URLs a procesar- **Pandas**: Análisis de datos

  --no-headless                 # Desactivar modo headless (debug)- **Pytest**: Testing

```

---

### Variables de Entorno

## 📄 Licencia

Crear archivo `.env` (opcional):

MIT License

```bash

# Base de datos---

DATABASE_PATH=database/price_monitor.db

## 📞 Más Información

# Scraping

DEFAULT_CACHE_HOURS=24Ver **[README_V3.md](README_V3.md)** para documentación completa.

DEFAULT_DAYS_AHEAD=30

DEFAULT_NIGHTS=2---



# Logging**Autor**: Aoneken  

LOG_LEVEL=INFO**Última actualización**: 2025-01-08  

LOG_FILE=logs/scheduler_v3.log**Branch**: v3  

```**Commits**: Ver `git log --oneline`



------



## 🧪 Testing## Legacy (V1/V2)



### Tests Unitarios (Parsers)El código de versiones anteriores se encuentra en `legacy/` para referencia histórica.



```bashEstado V3 (rama `v3`): Skeleton mínimo activado.

# Todos los tests

pytest tests_v3/ -v- Núcleo conservado: Solo la tabla `Establecimientos` (schema mínimo en `database/schema.sql`).

- Documentación constitucional: ver `docs_v3/` (arquitectura, dominio, contratos y migración).

# Solo una plataforma- Código V1/V2 reubicado en `legacy/` para referencia histórica y comparativa.

pytest tests_v3/test_parsers_airbnb.py -v- A partir de aquí, se reconstruirá la app conforme a los contratos definidos en V3.



# Con coberturaDocumentación V3 (índice):

pytest tests_v3/ --cov=src/parsers- `docs_v3/VISION_NEGOCIO_V3.md`

```- `docs_v3/FASE_0_CONSTITUCION_Y_MIGRACION.md`

- `docs_v3/FASE_1_DATOS_Y_DOMINIO.md`

### Tests de Integración- `docs_v3/FASE_2_INGESTA_Y_SCRAPING.md`

- `docs_v3/FASE_3_PERSISTENCIA_Y_NORMALIZACION.md`

```bash- `docs_v3/FASE_4_OBSERVABILIDAD_Y_TESTING.md`

# Test rápido con 1 URL real- `docs_v3/FASE_5_UI_Y_API.md`

python tests_v3/test_scheduler_quick.py- `docs_v3/FASE_6_SEGURIDAD_Y_OPERACION.md`



# Test específico de Booking---

python tests_v3/test_booking_quick.py

**Sistema de Inteligencia de Precios para Plataformas de Alojamiento**

# Test de establecimiento específico

python tests_v3/test_viento_glaciares.pyPrice Monitor es una aplicación web interna que permite gestionar un portafolio de establecimientos, automatizar el scraping de precios en plataformas como Booking y Airbnb, y visualizar insights de pricing y ocupación.

```

---

### Demo del SDK

## 🎯 Características Principales (Legacy)

```bash

python scripts/demo_v3.py- **🏠 Gestión de Establecimientos**: CRUD completo para administrar propiedades y URLs de monitoreo

# Seleccionar opción 1: Demo de parsers con fixtures HTML- **🤖 Scraping Automatizado**: Extracción inteligente de precios con lógica 3→2→1 noches

```- **💾 Base de Datos Histórica**: SQLite optimizado con índices y esquema normalizado

- **📊 Dashboard Interactivo**: Visualización de tendencias de precios y ocupación

---- **🔒 Anti-Detección**: Modo stealth con Playwright para evitar bloqueos

- **⏱️ Lógica de Frescura**: Solo actualiza datos > 48 horas (configurable)

## 📊 Arquitectura V3

---

### Flujo de Datos

## 🏗️ Arquitectura (Legacy)

```

URL + Fechas Nota: La arquitectura detallada a continuación corresponde al legado V1/V2. El diseño vigente para V3 está en `docs_v3/ARQUITECTURA_V3.md`. La implementación V3 se irá incorporando gradualmente.

    ↓

Robot (Playwright) → Navegación + HTML### Stack Tecnológico

    ↓

Parser → Extracción de datos- **Frontend**: Streamlit (interfaz web interactiva)

    ↓- **Backend**: Python 3.11+

Normalizer → Validación + Normalización- **Base de Datos**: SQLite con esquema normalizado (3 tablas)

    ↓- **Scraping**: Playwright con modo stealth

Quote (objeto Python) → Quality Score- **Visualización**: Plotly para gráficos interactivos

    ↓

DatabaseAdapter → Persistencia en SQLite### Patrones de Diseño

    ↓

Base de Datos → Consultas y análisis- **Strategy Pattern**: Robots intercambiables por plataforma

```- **Factory Pattern**: Creación dinámica de robots

- **Singleton**: Gestor único de base de datos

### Contratos de Datos- **Repository Pattern**: Abstracción de acceso a datos



#### AirbnbQuote### Estructura del Proyecto (Legado en `legacy/`)

```python

{```

    'property_id': str,           # ID único de la propiedadprice-monitor/

    'check_in': date,            # Fecha de check-in├── legacy/                         # Código V1/V2 preservado

    'check_out': date,           # Fecha de check-out│   ├── app.py

    'nights': int,               # Número de noches│   ├── scrapers/

    'currency': str,             # 'USD', 'EUR', 'ARS', etc.│   ├── pages/

    'precio_total': float,       # Precio total de la estadía│   ├── ui/

    'precio_por_noche': float,   # Precio promedio por noche│   ├── tests/

    'incluye_desayuno': str,     # 'Sí' | 'No' | 'Desconocido'│   └── tests_root/

    'wifi_incluido': str,        # 'Sí' | 'No' | 'Desconocido'├── docs_v3/                        # Constitución y guías V3

    'fuente': str,               # 'dom_breakdown', 'dom_total', etc.├── config/

    'quality': float,            # 0.0 - 1.0 (confiabilidad)│   └── settings.py                 # Configuración centralizada

    'errores': list              # Lista de errores/advertencias└── database/

}  ├── schema.sql                  # (V3) Solo Establecimientos

```  └── db_manager.py               # (V3) CRUD mínimo

```

#### BookingQuote

```python---

{

    'property_id': str,## 🚀 Instalación

    'precio_total': float,        # Base + impuestos

    'precio_por_noche': float,### Requisitos Previos

    'impuestos_cargos_extra': float | None,

    'fuente': str,               # 'json_embedded', 'dom_fallback'- Python 3.11 o superior

    # ... resto común con Airbnb- pip (gestor de paquetes de Python)

}

```### Paso 1: Clonar el Repositorio



#### ExpediaQuote```bash

```pythongit clone https://github.com/tu-usuario/price-monitor.git

{cd price-monitor

    'property_id': str,```

    'precio_total_vigente': float,

    'precio_original_tachado': float | None,### Paso 2: Crear Entorno Virtual

    'monto_descuento': float | None,

    'porcentaje_descuento': float | None,```bash

    'fuente': str,               # 'dom_price', 'json_ld'python -m venv venv

    # ... resto común con Airbnbsource venv/bin/activate  # En Windows: venv\Scripts\activate

}```

```

### Paso 3: Instalar Dependencias

---

```bash

## 🛠️ Solución de Problemaspip install -r requirements.txt

```

### Error: "playwright not found"

```bash### Paso 4: Instalar Playwright

playwright install chromium

``````bash

playwright install chromium

### Error: "Database not found"```

```bash

# Verificar que existe database/price_monitor.db### Paso 5: Configurar Variables de Entorno

ls -l database/

```bash

# Si no existe, usar el schema legacycp .env.example .env

sqlite3 database/price_monitor.db < legacy/database/schema_completo.sql# Editar .env con tus configuraciones

``````



### Error: "No URLs activas"### Paso 6: Inicializar Base de Datos

- Ve a la página "Gestión de URLs" en la aplicación

- Crea un establecimientoLa base de datos se inicializa automáticamente al primer uso.

- Agrega URLs y actívalas

---

### Scraping muy lento

```bash## 💻 Uso

# Aumentar caché para evitar re-scraping

python scripts/scheduler_v3.py --cache-hours 48### Iniciar la Aplicación



# Limitar número de URLs```bash

python scripts/scheduler_v3.py --max-urls 5streamlit run app.py

``````



### Ver logs detalladosLa aplicación se abrirá en `http://localhost:8501`

```bash

tail -f logs/scheduler_v3.log### Flujo de Trabajo

```

1. **Establecimientos** (Pestaña 1)

### Selectores CSS desactualizados   - Crear un establecimiento

Los selectores pueden cambiar cuando las plataformas actualizan sus sitios. Si notas errores:   - Agregar URLs de Booking/Airbnb

1. Revisa `docs_v3/metodologias/` para la metodología de cada plataforma   - Activar/desactivar monitoreo

2. Actualiza los selectores en el parser correspondiente

3. Ejecuta tests para validar: `pytest tests_v3/test_parsers_*.py -v`2. **Scraping** (Pestaña 2)

   - Seleccionar establecimiento

---   - Definir rango de fechas

   - Iniciar scraping y ver progreso

## 📈 Roadmap

3. **Base de Datos** (Pestaña 3)

### ✅ Completado (V3.0)   - Explorar datos con filtros

- [x] SDK modular con parsers/robots/normalizers   - Exportar a CSV

- [x] Integración completa con base de datos

- [x] UI Streamlit funcional (Scraping + Monitoreo + Gestión)4. **Dashboard** (Pestaña 4)

- [x] Scheduler CLI con logging completo   - Visualizar gráficos de tendencias

- [x] Sistema de caché inteligente   - Comparar plataformas

- [x] Tests unitarios (26+ tests)   - Analizar KPIs

- [x] Filtros avanzados por plataforma y establecimiento

- [x] Quality scoring por fuente de datos---

- [x] Documentación completa

## ⚙️ Configuración

### 🔄 En Desarrollo (V3.1)

- [ ] Tests de integración con fixtures HTML### Archivo `.env`

- [ ] Validación exhaustiva con URLs reales de producción

- [ ] Dashboard de calidad de datos```env

- [ ] Exportación de reportes a CSV/Excel# Base de Datos

DATABASE_PATH=./database/price_monitor.db

### 📋 Planificado

- **V3.2**: Scraping concurrente (asyncio + Playwright async)# Scraping

- **V3.3**: Alertas de cambios de precio (email/Telegram/Slack)SCRAPER_MIN_DELAY=3

- **V3.4**: API REST sobre el orchestratorSCRAPER_MAX_DELAY=8

- **V3.5**: Soporte para más plataformas (Vrbo, Hotels.com, Despegar)SCRAPER_MAX_RETRIES=3

- **V3.6**: Machine Learning para predicción de preciosSCRAPER_HEADLESS=True

- **V3.7**: Integración con PMS (sistemas de gestión hotelera)

# Frescura de Datos

---DATA_FRESHNESS_HOURS=48

```

## 🤝 Contribución

### Selectores CSS

Contribuciones son bienvenidas! Por favor:

Los selectores se configuran en `scrapers/config/selectors.json`. Esto permite actualizar selectores sin tocar el código.

1. Fork del repositorio

2. Crear branch feature (`git checkout -b feature/nueva-funcionalidad`)Ejemplo:

3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)```json

4. Push al branch (`git push origin feature/nueva-funcionalidad`){

5. Crear Pull Request  "Booking": {

    "precio": [

### Guías de Contribución      "[data-testid='price-label']",

- Sigue PEP 8 para código Python      ".priceDisplay"

- Agrega tests para nuevas funcionalidades    ],

- Actualiza documentación según corresponda    "no_disponible": [

- Usa commits descriptivos (formato: `type: description`)      "[data-testid='calendar-unavailable']"

    ]

---  }

}

## 📚 Documentación Adicional```



### Para Usuarios---

- **[docs_v3/SDK_V3_README.md](docs_v3/SDK_V3_README.md)**: Documentación completa del SDK

- **[docs_v3/executive/](docs_v3/executive/)**: Documentos ejecutivos y resúmenes## 🤖 Agregar Nuevas Plataformas



### Para Desarrolladores### 1. Crear el Robot

- **[docs_v3/FASE_*.md](docs_v3/)**: Documentación técnica por fases

- **[docs_v3/metodologias/](docs_v3/metodologias/)**: Metodologías de scraping por plataforma```python

- **[CHANGELOG.md](CHANGELOG.md)**: Historial de cambios# scrapers/robots/vrbo_robot.py

from scrapers.base_robot import BaseRobot

### Legacy (V1/V2)

El código de versiones anteriores se encuentra en `legacy/` para referencia histórica.class VrboRobot(BaseRobot):

    def __init__(self):

---        super().__init__('Vrbo')

        self._cargar_selectores()

## 🔐 Seguridad y Privacidad    

    def buscar(self, browser, url_base, fecha_checkin):

- **Datos locales**: Toda la información se almacena en SQLite local        # Implementar lógica de scraping

- **Sin API keys de terceros**: No se requieren credenciales de plataformas        pass

- **Modo stealth**: Navegación que minimiza detección    

- **Rate limiting**: Delays configurables entre peticiones    def construir_url(self, url_base, fecha_checkin, noches):

        return URLBuilder.vrbo_url(url_base, fecha_checkin, noches)

**⚠️ Nota Legal**: Este software es para uso educativo e interno. El scraping puede violar los términos de servicio de las plataformas. Úsalo bajo tu propia responsabilidad y respetando las políticas de robots.txt.```



---### 2. Registrar en el Factory



## 📄 Licencia```python

# scrapers/robot_factory.py

MIT License - Ver [LICENSE](LICENSE) para detallesfrom scrapers.robots.vrbo_robot import VrboRobot



---class RobotFactory:

    _robots = {

## 📞 Soporte        'Booking': BookingRobot,

        'Airbnb': AirbnbRobot,

- **Issues**: [GitHub Issues](https://github.com/Aoneken/price-monitor/issues)        'Vrbo': VrboRobot,  # Agregar aquí

- **Documentación**: `docs_v3/`    }

- **Email**: comercial@aoneken.com```



---### 3. Agregar Selectores



## 🙏 Agradecimientos```json

// scrapers/config/selectors.json

- **Streamlit**: Framework de UI interactivo{

- **Playwright**: Herramienta de scraping robusta  "Vrbo": {

- **SQLite**: Base de datos embebida eficiente    "precio": ["[data-testid='price']"],

- **Pandas**: Análisis de datos    "no_disponible": ["text=/not available/i"]

- **Plotly**: Visualizaciones interactivas  }

}

---```



**Versión**: 3.0.0  ### 4. Actualizar Constraint de BD

**Última actualización**: 2025-11-07  

**Branch**: v3  ```sql

**Status**: ✅ Producción Ready  -- database/schema.sql

**Autor**: AonekenCHECK(plataforma IN ('Booking', 'Airbnb', 'Vrbo'))

```

---

---

**🏗️ Sistema de Inteligencia de Precios para Plataformas de Alojamiento**

## 🧪 Testing

Price Monitor es una aplicación web interna que permite gestionar un portafolio de establecimientos, automatizar el scraping de precios en plataformas de alojamiento, y visualizar insights de pricing y ocupación para toma de decisiones basada en datos.

```bash
# Ejecutar tests
python -m pytest tests/

# Con cobertura
python -m pytest tests/ --cov=scrapers --cov=database
```

---

## 📊 Base de Datos

### Esquema

```
Establecimientos (id_establecimiento, nombre_personalizado, fecha_creacion)
    ↓
Plataformas_URL (id_plataforma_url, id_establecimiento, plataforma, url, esta_activa)
    ↓
Precios (id_plataforma_url, fecha_noche, precio_base, esta_ocupado, fecha_scrape, ...)
```

### Lógica de Negocio

- **UPSERT**: Inserta o actualiza precios según clave primaria compuesta (URL + Fecha)
- **Lógica 48h**: Solo actualiza datos con > 48 horas de antigüedad
- **Lógica 3→2→1**: Busca disponibilidad para 3, 2 y 1 noche(s) en ese orden
- **Ocupación**: Si precio = 0, se asume `esta_ocupado = TRUE`

---

## 🔐 Seguridad y Buenas Prácticas

### Anti-Detección

- User-Agent rotation
- Headless mode configurable
- Random delays entre peticiones (3-8s)
- Exponential backoff en reintentos
- Stealth mode con Playwright

### Rate Limiting

```python
# Configurado en .env
SCRAPER_MIN_DELAY=3
SCRAPER_MAX_DELAY=8
```

### Limitaciones

- **SQLite**: Máximo 5 usuarios simultáneos (para más, migrar a PostgreSQL)
- **Bloqueos**: Los sitios pueden detectar scraping intensivo
- **Selectores**: Pueden cambiar sin aviso (mantenimiento periódico necesario)

---

## 🐛 Troubleshooting

### Error: "Playwright not installed"

```bash
playwright install chromium
```

### Error: "Database is locked"

SQLite no soporta múltiples escrituras simultáneas. Espera a que termine la operación actual.

### Error: "CAPTCHA detected"

- Reduce la frecuencia de scraping (aumenta delays)
- Usa `SCRAPER_HEADLESS=False` para debugging
- Verifica que stealth mode esté activo

### Selectores no funcionan

1. Abre `scrapers/config/selectors.json`
2. Actualiza selectores inspeccionando la página web
3. Agrega selectores alternativos para redundancia

---

## 🗺️ Roadmap

### Versión 1.0 (MVP) ✅
- [x] CRUD de establecimientos
- [x] Scraping de Booking y Airbnb
- [x] Dashboard básico
- [x] Lógica de 48h y 3→2→1

### Versión 1.1 (En desarrollo)
- [ ] Soporte para Vrbo
- [ ] Tests automatizados
- [ ] Logging avanzado
- [ ] Notificaciones por email

### Versión 2.0 (Futuro)
- [ ] Módulo de análisis competitivo
- [ ] Recomendaciones de pricing con IA
- [ ] Integración con PMS
- [ ] API REST

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaPlataforma`)
3. Commit tus cambios (`git commit -m 'Add Vrbo support'`)
4. Push a la rama (`git push origin feature/NuevaPlataforma`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

---

## 📞 Contacto

Para preguntas o soporte, contacta al equipo de desarrollo.

---

## 🙏 Agradecimientos

- **Streamlit**: Framework de UI
- **Playwright**: Herramienta de scraping
- **Plotly**: Visualizaciones interactivas

---

**Nota**: Este software es para uso educativo e interno. El scraping puede violar los términos de servicio de las plataformas. Úsalo bajo tu propia responsabilidad y respetando las políticas de robots.txt.
