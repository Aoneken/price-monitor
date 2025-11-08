# Price Monitor Web App — Diseño y Especificación Técnica (v0.1)

Fecha: 2025-11-08
Autoría: Proyecto price-monitor

## 1. objetivo y alcance

Construir una aplicación web local para monitorear precios y disponibilidad de alojamientos en múltiples plataformas (Airbnb, Booking, Expedia, etc.), organizada por espacios de trabajo y temporadas.

- Local-first: corre localmente, sin dependencias cloud obligatorias.
- Realtime: cada acción en la UI impacta y persiste de inmediato en la base de datos.
- Escalable en fuentes: hoy Airbnb con script funcional; luego Booking/Expedia y más.
- Extensible: añadir nuevos scraping providers y tareas sin romper la UI.

No-objetivos (v0.1):

- No haremos scraping distribuido ni masivo; enfoque en uso local controlado.
- No integramos pasarelas de pago ni dashboards de BI complejos (posible export CSV/JSON).

## 2. conceptos clave (dominio)

- Workspace (Espacio de trabajo): contenedor lógico (ej.: “Comarca Lago del Desierto”).
- Season (Temporada): ventana temporal fija (start_date, end_date) dentro de un Workspace. Pueden existir varias.
- Establishment (Establecimiento): entidad administrable, con metadatos y URLs base por plataforma (Airbnb, Booking, Expedia...).
- PlatformSource: URL base + metadata específica de cada plataforma por establecimiento.
- ScrapeJob: ejecución de scraping (parámetros: periodo, huéspedes, moneda, locale, provider, concurrencia, etc.).
- PriceSnapshot: resultado atómico (por día) de disponibilidad/precio con notas, moneda y timestamp.

## 3. flujo de usuario (MVP)

1. Crear Workspace → Crear Season (definir periodo) → Gestionar Establishments (CRUD) y asignar URL base por plataforma.
2. En pestaña “Scraping”: seleccionar Season y Establishments, setear parámetros (huéspedes, moneda, locale, delay/retries/concurrency) y lanzar.
3. Progreso en tiempo real por establecimiento (barra y logs). Posibilidad de cancelar.
4. Resultados persisten en DB; se pueden exportar CSV/JSON.

## 4. arquitectura

- Frontend: SPA ligera (React/Vite) o servidor de templates (FastAPI + Jinja2) — MVP puede usar HTMX/Alpine.
- Backend: FastAPI (Python 3.10+). Endpoints REST + WebSocket para progreso.
- Workers: procesos/threads gestionados por el backend para lanzar scrapings (ThreadPool con límites, similar al script actual).
- DB: PostgreSQL (preferido) o SQLite para MVP local. SQLAlchemy + Alembic para migraciones.
- Librería interna: `price_monitor` (módulos core/providers) reusada por CLI y backend.

## 5. modelo de datos (SQL, propuesta)

- workspaces (id, name, created_at)
- seasons (id, workspace_id FK, name, start_date, end_date, created_at)
- establishments (id, workspace_id FK, name, notes, created_at)
- platform_sources (id, establishment_id FK, platform ENUM['airbnb','booking','expedia',...], base_url TEXT, metadata JSONB, created_at)
- scrape_jobs (id, season_id FK, params JSONB, status ENUM['queued','running','done','error','canceled'], started_at, finished_at, summary JSONB)
- price_snapshots (id, scrape_job_id FK, establishment_id FK, platform, date, available BOOL, available_checkin BOOL, available_checkout BOOL, bookable BOOL, min_nights INT, max_nights INT, price_per_night NUMERIC, price_basis_nights INT, stay_total NUMERIC, currency TEXT, inserted_at TIMESTAMP, notes TEXT)
- indices recomendados por (season_id, establishment_id, date) y por (scrape_job_id).

## 6. API (REST + WS, MVP)

- POST /api/workspaces {name}
- GET /api/workspaces
- POST /api/workspaces/{wid}/seasons {name,start_date,end_date}
- GET /api/workspaces/{wid}/seasons
- CRUD /api/workspaces/{wid}/establishments
- CRUD /api/establishments/{eid}/platform-sources
- POST /api/seasons/{sid}/scrape (body: establishments[], platform, params)
- GET /api/scrape-jobs/{job_id}
- GET /api/seasons/{sid}/snapshots?establishment_id=&platform=&date_from=&date_to=
- WS /ws/scrape-jobs/{job_id} → eventos de progreso en tiempo real

`params` incluye: guests, currency, locale, delay, retries, concurrency, cache_hours, feature flags (e.g., disable rich, etc.).

## 7. integración con scraping actual (Airbnb)

- Reusar funciones existentes de `scrape_real_prices.py` moviéndolas a `price_monitor/core` y `price_monitor/providers/airbnb.py`.
- Mantener el “entrypoint” CLI para usos fuera de la web app.
- Backend lanza jobs con las mismas funciones, registrando progreso y guardando `price_snapshots` en DB.
- Caching: respetar `cache_hours` y congelar filas históricas.

## 8. manejo de cambios en plataformas

- Centralizar constantes/headers/hashes por provider (p. ej., `CALENDAR_HASH`) en `providers/airbnb.py`.
- Feature flags y config en DB/ENV para rotar valores sin redeploy.
- Validar respuestas y fallbacks (retries con backoff + jitter). Alertas en logs.

## 9. seguridad y cumplimiento

- Respeto a Términos de Uso: uso personal/local; control de tasa (delay/concurrency caps).
- Sanitización de entrada (URLs) y validaciones de parámetros.
- No almacenar credenciales sensibles en texto plano (ENV variables).
- CORS local y CSRF si se habilitan formularios.

## 10. observabilidad

- Logging estructurado (JSON) + niveles (info, warning, error).
- Métricas por job: duración, requests, retries, % días con precio, errores.
- Export de reportes (CSV/JSON) y pequeño resumen en UI.

## 11. ejecución local (MVP)

- Requisitos: Python 3.10+, PostgreSQL/SQLite.
- Instalar: `pip install -r requirements.txt`
- Migraciones: `alembic upgrade head` (si se usa PostgreSQL/SQLite con SQLAlchemy).
- Correr backend: `uvicorn app.main:app --reload`
- UI: servidor de templates o Vite dev server.

## 12. roadmap

- v0.1: CRUD Workspaces/Seasons/Establishments/PlatformSources, lanzar job Airbnb, progreso y snapshots persistidos, export CSV.
- v0.2: Booking/Expedia provider; filtros y comparaciones.
- v0.3: Agenda de corridas, notificaciones locales, dashboards simples.

## 13. criterios de aceptación (MVP)

- Crear workspace + temporada y agregar al menos 3 establecimientos con URLs válidas.
- Lanzar scraping Airbnb para un rango de fechas y huéspedes; ver progreso en tiempo real.
- Persistencia de snapshots y export CSV sin errores.
- Capacidad de repetir job cambiando parámetros (currency, locale, delay, retries, concurrency) sin modificar código.

## 14. apéndice: formatos de URL base (ejemplos)

- Airbnb: `https://www.airbnb.com.ar/rooms/{listing_id}` (p. ej., `.../rooms/39250879`)
- Booking: URL pública de la propiedad (ej.: `https://www.booking.com/hotel/ar/cerro-electrico.es.html`)
- Expedia: URL pública de info hotel (ej.: `https://www.expedia.com/es/El-Chalten-Hoteles-...Informacion-Hotel`)

Nota: Para cada provider se almacenarán campos de normalización (p. ej., `listing_id` para Airbnb) derivados de la URL base.
