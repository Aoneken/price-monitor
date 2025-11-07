# 📊 Price Monitor V3

> **⚠️ IMPORTANTE**: Este proyecto está en la rama `v3` con implementación completa del SDK V3.  
> Para documentación completa, ver **[README_V3.md](README_V3.md)**

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# Iniciar aplicación
streamlit run app.py

# Ejecutar scraping automático
python scheduler_v3.py --help
```

---

## ✨ Novedades V3

### SDK Completo
- ✅ **Parsers modulares** por plataforma (Airbnb, Booking, Expedia)
- ✅ **Robots con Playwright** y configuración stealth
- ✅ **Normalizers** para datos multi-divisa y validación
- ✅ **Orchestrator** para coordinación multi-plataforma
- ✅ **Quality scoring** (0-1) por confiabilidad de fuente

### Aplicación Web
- ✅ **Scraping V3**: UI para scraping manual con configuración flexible
- ✅ **Monitoreo V3**: Dashboard con métricas en tiempo real
- ✅ **Sistema de caché**: Evita re-scraping innecesario (24h default)
- ✅ **Logging completo**: logs/scheduler_v3.log

### Automatización
- ✅ **Scheduler CLI**: Ejecución batch desde terminal
- ✅ **Integración con BD**: Mapeo automático a schema legacy
- ✅ **Filtrado por plataforma**: Scraping selectivo
- ✅ **Tests unitarios**: 26 tests, 100% passing

---

## 📁 Documentación

### Para Usuarios
- **[README_V3.md](README_V3.md)**: Guía completa de uso
- **[SDK_V3_README.md](SDK_V3_README.md)**: Documentación del SDK

### Para Desarrolladores
- **[IMPLEMENTACION_SDK_V3_COMPLETA.md](IMPLEMENTACION_SDK_V3_COMPLETA.md)**: Resumen técnico
- **docs_v3/metodologias/**: Metodologías por plataforma
- **tests_v3/**: Suite de tests unitarios

---

## 🎯 Estado del Proyecto

**Versión**: 3.0.0  
**Branch**: v3  
**Status**: ✅ **Producción Ready**

### Completado
- [x] SDK V3 con parsers, robots, normalizers
- [x] Integración completa con base de datos
- [x] UI Streamlit funcional (Scraping + Monitoreo)
- [x] Scheduler CLI con logging
- [x] Sistema de caché inteligente
- [x] Tests unitarios (26 tests, 100% passing)

### En Progreso
- [ ] Tests de integración con fixtures HTML
- [ ] Validación con URLs reales de producción

### Roadmap
- [ ] Scraping concurrente (asyncio)
- [ ] Alertas de cambios de precio
- [ ] API REST
- [ ] Soporte para más plataformas

---

## 🏗️ Arquitectura V3

```
src/
├── parsers/          # Extracción de datos HTML
├── robots/           # Navegación Playwright
├── normalizers/      # Normalización y validación
├── persistence/      # Integración con BD
└── orchestrator_v3   # Coordinador multi-plataforma
```

**Flujo de Datos**:
```
URL + Fechas → Robot (Playwright) → HTML → Parser → Normalizer → Quote → BD
```

---

## 📊 Características Principales (V3)

### 🤖 Scraping Inteligente
- **3 plataformas**: Airbnb, Booking, Expedia
- **Playwright**: Navegación robusta y stealth
- **Quality scoring**: Confiabilidad 0-1 por fuente
- **Manejo de errores**: Códigos específicos por plataforma

### 📈 Monitoreo en Tiempo Real
- **Métricas generales**: Total precios, actividad 24h, cobertura
- **Distribución**: URLs con datos por plataforma
- **Actividad reciente**: 50 últimos scrapeos con estado
- **Tendencias**: Gráficos históricos 30 días

### 🗄️ Base de Datos
- **SQLite** optimizado con índices
- **Caché inteligente**: Configurable (default 24h)
- **Histórico completo**: Precios por noche
- **Tracking de errores**: Para diagnóstico

---

## 🚀 Uso Rápido

### Interfaz Web
```bash
streamlit run app.py
```
Ir a:
- **"Scraping V3"**: Ejecutar scraping manual
- **"Monitoreo V3"**: Ver métricas y tendencias

### CLI (Automatización)
```bash
# Scrapear todas las URLs
python scheduler_v3.py

# Solo una plataforma
python scheduler_v3.py --platform Airbnb

# Configuración personalizada
python scheduler_v3.py --days-ahead 60 --nights 3 --cache-hours 48
```

### Tests
```bash
# Tests unitarios
pytest tests_v3/ -v

# Demo SDK (sin navegación)
python demo_v3.py

# Test rápido (1 URL real)
python test_scheduler_quick.py
```

---

## 📦 Estructura del Proyecto

```
price-monitor/
├── src/                    # SDK V3
│   ├── parsers/           # Airbnb, Booking, Expedia
│   ├── robots/            # Navegación Playwright
│   ├── normalizers/       # Normalización de datos
│   ├── persistence/       # Integración BD
│   └── orchestrator_v3.py
├── pages/                  # UI Streamlit
│   ├── 6_Scraping_V3.py
│   └── 7_Monitoreo_V3.py
├── tests_v3/              # Tests unitarios
├── database/              # SQLite DB
├── docs_v3/               # Documentación
├── logs/                  # Logs de ejecución
├── scheduler_v3.py        # CLI scheduler
├── demo_v3.py            # Demo del SDK
└── app.py                # App principal
```

---

## 🔧 Tecnologías

- **Python 3.12+**
- **Streamlit 1.29**: Interfaz web
- **Playwright 1.48**: Scraping con navegador
- **SQLite**: Base de datos
- **Pandas**: Análisis de datos
- **Pytest**: Testing

---

## 📄 Licencia

MIT License

---

## 📞 Más Información

Ver **[README_V3.md](README_V3.md)** para documentación completa.

---

**Autor**: Aoneken  
**Última actualización**: 2025-01-08  
**Branch**: v3  
**Commits**: Ver `git log --oneline`

---

## Legacy (V1/V2)

El código de versiones anteriores se encuentra en `legacy/` para referencia histórica.

Estado V3 (rama `v3`): Skeleton mínimo activado.

- Núcleo conservado: Solo la tabla `Establecimientos` (schema mínimo en `database/schema.sql`).
- Documentación constitucional: ver `docs_v3/` (arquitectura, dominio, contratos y migración).
- Código V1/V2 reubicado en `legacy/` para referencia histórica y comparativa.
- A partir de aquí, se reconstruirá la app conforme a los contratos definidos en V3.

Documentación V3 (índice):
- `docs_v3/VISION_NEGOCIO_V3.md`
- `docs_v3/FASE_0_CONSTITUCION_Y_MIGRACION.md`
- `docs_v3/FASE_1_DATOS_Y_DOMINIO.md`
- `docs_v3/FASE_2_INGESTA_Y_SCRAPING.md`
- `docs_v3/FASE_3_PERSISTENCIA_Y_NORMALIZACION.md`
- `docs_v3/FASE_4_OBSERVABILIDAD_Y_TESTING.md`
- `docs_v3/FASE_5_UI_Y_API.md`
- `docs_v3/FASE_6_SEGURIDAD_Y_OPERACION.md`

---

**Sistema de Inteligencia de Precios para Plataformas de Alojamiento**

Price Monitor es una aplicación web interna que permite gestionar un portafolio de establecimientos, automatizar el scraping de precios en plataformas como Booking y Airbnb, y visualizar insights de pricing y ocupación.

---

## 🎯 Características Principales (Legacy)

- **🏠 Gestión de Establecimientos**: CRUD completo para administrar propiedades y URLs de monitoreo
- **🤖 Scraping Automatizado**: Extracción inteligente de precios con lógica 3→2→1 noches
- **💾 Base de Datos Histórica**: SQLite optimizado con índices y esquema normalizado
- **📊 Dashboard Interactivo**: Visualización de tendencias de precios y ocupación
- **🔒 Anti-Detección**: Modo stealth con Playwright para evitar bloqueos
- **⏱️ Lógica de Frescura**: Solo actualiza datos > 48 horas (configurable)

---

## 🏗️ Arquitectura (Legacy)

Nota: La arquitectura detallada a continuación corresponde al legado V1/V2. El diseño vigente para V3 está en `docs_v3/ARQUITECTURA_V3.md`. La implementación V3 se irá incorporando gradualmente.

### Stack Tecnológico

- **Frontend**: Streamlit (interfaz web interactiva)
- **Backend**: Python 3.11+
- **Base de Datos**: SQLite con esquema normalizado (3 tablas)
- **Scraping**: Playwright con modo stealth
- **Visualización**: Plotly para gráficos interactivos

### Patrones de Diseño

- **Strategy Pattern**: Robots intercambiables por plataforma
- **Factory Pattern**: Creación dinámica de robots
- **Singleton**: Gestor único de base de datos
- **Repository Pattern**: Abstracción de acceso a datos

### Estructura del Proyecto (Legado en `legacy/`)

```
price-monitor/
├── legacy/                         # Código V1/V2 preservado
│   ├── app.py
│   ├── scrapers/
│   ├── pages/
│   ├── ui/
│   ├── tests/
│   └── tests_root/
├── docs_v3/                        # Constitución y guías V3
├── config/
│   └── settings.py                 # Configuración centralizada
└── database/
  ├── schema.sql                  # (V3) Solo Establecimientos
  └── db_manager.py               # (V3) CRUD mínimo
```

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/price-monitor.git
cd price-monitor
```

### Paso 2: Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Instalar Playwright

```bash
playwright install chromium
```

### Paso 5: Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### Paso 6: Inicializar Base de Datos

La base de datos se inicializa automáticamente al primer uso.

---

## 💻 Uso

### Iniciar la Aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

### Flujo de Trabajo

1. **Establecimientos** (Pestaña 1)
   - Crear un establecimiento
   - Agregar URLs de Booking/Airbnb
   - Activar/desactivar monitoreo

2. **Scraping** (Pestaña 2)
   - Seleccionar establecimiento
   - Definir rango de fechas
   - Iniciar scraping y ver progreso

3. **Base de Datos** (Pestaña 3)
   - Explorar datos con filtros
   - Exportar a CSV

4. **Dashboard** (Pestaña 4)
   - Visualizar gráficos de tendencias
   - Comparar plataformas
   - Analizar KPIs

---

## ⚙️ Configuración

### Archivo `.env`

```env
# Base de Datos
DATABASE_PATH=./database/price_monitor.db

# Scraping
SCRAPER_MIN_DELAY=3
SCRAPER_MAX_DELAY=8
SCRAPER_MAX_RETRIES=3
SCRAPER_HEADLESS=True

# Frescura de Datos
DATA_FRESHNESS_HOURS=48
```

### Selectores CSS

Los selectores se configuran en `scrapers/config/selectors.json`. Esto permite actualizar selectores sin tocar el código.

Ejemplo:
```json
{
  "Booking": {
    "precio": [
      "[data-testid='price-label']",
      ".priceDisplay"
    ],
    "no_disponible": [
      "[data-testid='calendar-unavailable']"
    ]
  }
}
```

---

## 🤖 Agregar Nuevas Plataformas

### 1. Crear el Robot

```python
# scrapers/robots/vrbo_robot.py
from scrapers.base_robot import BaseRobot

class VrboRobot(BaseRobot):
    def __init__(self):
        super().__init__('Vrbo')
        self._cargar_selectores()
    
    def buscar(self, browser, url_base, fecha_checkin):
        # Implementar lógica de scraping
        pass
    
    def construir_url(self, url_base, fecha_checkin, noches):
        return URLBuilder.vrbo_url(url_base, fecha_checkin, noches)
```

### 2. Registrar en el Factory

```python
# scrapers/robot_factory.py
from scrapers.robots.vrbo_robot import VrboRobot

class RobotFactory:
    _robots = {
        'Booking': BookingRobot,
        'Airbnb': AirbnbRobot,
        'Vrbo': VrboRobot,  # Agregar aquí
    }
```

### 3. Agregar Selectores

```json
// scrapers/config/selectors.json
{
  "Vrbo": {
    "precio": ["[data-testid='price']"],
    "no_disponible": ["text=/not available/i"]
  }
}
```

### 4. Actualizar Constraint de BD

```sql
-- database/schema.sql
CHECK(plataforma IN ('Booking', 'Airbnb', 'Vrbo'))
```

---

## 🧪 Testing

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
