# Web Application - Quick Start

## 🚀 Lanzar la aplicación web

### Opción 1: Via VS Code Task (recomendado)
1. Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac)
2. Escribe "Tasks: Run Task"
3. Selecciona "run-webapp"

### Opción 2: Línea de comandos
```bash
.venv/bin/python run_webapp.py
```

## 🌐 Acceso

La aplicación estará disponible en: **http://localhost:8000**

## 📖 Uso de la interfaz web

### 1. Agregar establecimientos
- En la página principal, usa el formulario "Agregar Establecimiento"
- Campos:
  - **ID de Airbnb**: El identificador numérico del listing
  - **Nombre**: Nombre descriptivo del establecimiento
  - **URL**: (Opcional) Link completo al listing

### 2. Iniciar scraping
- Haz clic en el botón "🔍 Scrape" en la tarjeta del establecimiento
- Completa el formulario:
  - **Fecha inicio**: YYYY-MM-DD
  - **Fecha fin**: YYYY-MM-DD
  - **Huéspedes**: Número de personas
- El scraping se ejecuta en segundo plano
- Verás el estado actualizado (pending → running → completed)

### 3. Ver precios
- Haz clic en "📊 Ver Precios" en la tarjeta del establecimiento
- Visualiza:
  - Gráfico de evolución de precios
  - Tabla detallada con disponibilidad y precios por fecha

## 🔌 API REST

### Endpoints disponibles

#### Listings
```bash
# Listar todos
GET /api/listings

# Crear nuevo
POST /api/listings
Content-Type: application/json
{
  "listing_id": "1413234233737891700",
  "name": "Viento de Glaciares",
  "url": "https://www.airbnb.com.ar/rooms/1413234233737891700"
}

# Obtener uno
GET /api/listings/{id}
```

#### Scrape Jobs
```bash
# Crear job (inicia scraping en background)
POST /api/scrape
Content-Type: application/json
{
  "listing_id": 1,
  "start_date": "2025-12-01",
  "end_date": "2025-12-15",
  "guests": 2
}

# Ver estado del job
GET /api/jobs/{job_id}
```

#### Precios
```bash
# Obtener precios de un listing en un rango
GET /api/prices/{listing_id}?start_date=2025-12-01&end_date=2025-12-15
```

## 💾 Base de datos

La aplicación usa SQLite (`price_monitor.db`) que se crea automáticamente al iniciar.

### Schema:
- **listings**: Establecimientos registrados
- **price_records**: Datos de disponibilidad y precios
- **scrape_jobs**: Historial de trabajos de scraping

## 🧪 Testing de la API

```bash
# Agregar un listing
curl -X POST http://localhost:8000/api/listings \
  -H "Content-Type: application/json" \
  -d '{"listing_id":"39250879","name":"Cerro Eléctrico","url":"https://www.airbnb.com.ar/rooms/39250879"}'

# Iniciar scraping
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"listing_id":1,"start_date":"2025-12-01","end_date":"2025-12-05","guests":2}'

# Verificar estado (espera unos segundos)
curl http://localhost:8000/api/jobs/1

# Ver precios guardados
curl "http://localhost:8000/api/prices/1?start_date=2025-12-01&end_date=2025-12-05"
```

## 🎯 Funcionalidades implementadas

✅ Interfaz web responsive con HTMX  
✅ API REST completa (FastAPI)  
✅ Base de datos SQLite con SQLAlchemy  
✅ Background tasks para scraping asíncrono  
✅ Visualización de precios con Chart.js  
✅ Integración completa con el scraper existente  
✅ Caching de precios históricos  

## 🚧 Próximas mejoras

- [ ] Autenticación de usuarios
- [ ] Alertas por email cuando cambian precios
- [ ] Exportar precios a Excel/CSV desde la UI
- [ ] Dashboard de comparación entre establecimientos
- [ ] Soporte para múltiples proveedores (Booking, Expedia)
- [ ] Configuración de temporadas personalizadas
