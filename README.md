# 📊 Price Monitor

**Sistema de Inteligencia de Precios para Plataformas de Alojamiento**

Price Monitor es una aplicación web interna que permite gestionar un portafolio de establecimientos, automatizar el scraping de precios en plataformas como Booking y Airbnb, y visualizar insights de pricing y ocupación.

---

## 🎯 Características Principales

- **🏠 Gestión de Establecimientos**: CRUD completo para administrar propiedades y URLs de monitoreo
- **🤖 Scraping Automatizado**: Extracción inteligente de precios con lógica 3→2→1 noches
- **💾 Base de Datos Histórica**: SQLite optimizado con índices y esquema normalizado
- **📊 Dashboard Interactivo**: Visualización de tendencias de precios y ocupación
- **🔒 Anti-Detección**: Modo stealth con Playwright para evitar bloqueos
- **⏱️ Lógica de Frescura**: Solo actualiza datos > 48 horas (configurable)

---

## 🏗️ Arquitectura

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

### Estructura del Proyecto

```
price-monitor/
├── app.py                          # Punto de entrada de Streamlit
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py                 # Configuración centralizada
├── database/
│   ├── schema.sql                  # DDL con índices
│   └── db_manager.py               # Gestor de BD con UPSERT
├── scrapers/
│   ├── base_robot.py               # Interfaz abstracta
│   ├── robot_factory.py            # Factory de robots
│   ├── orchestrator.py             # Orquestador principal
│   ├── robots/
│   │   ├── booking_robot.py
│   │   └── airbnb_robot.py
│   ├── config/
│   │   └── selectors.json          # Selectores CSS externos
│   └── utils/
│       ├── stealth.py              # Anti-detección
│       ├── url_builder.py          # Constructor de URLs
│       └── retry.py                # Lógica de reintentos
└── ui/
    └── pages/
        ├── 1_Establecimientos.py
        ├── 2_Scraping.py
        ├── 3_Base_de_Datos.py
        ├── 4_Dashboard.py
        └── 5_Analisis.py
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
