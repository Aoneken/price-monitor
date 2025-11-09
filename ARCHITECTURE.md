# Arquitectura técnica — Price Monitor

Este documento define de forma concisa los límites y contratos técnicos del proyecto. La visión del producto está en `VISION.md` y el estado / roadmap técnico en `PROJECT_STATUS.md`. Evitamos duplicación: este archivo se centra en estructura, responsabilidades, interfaces y puntos claros de extensión.

## Objetivo y audiencia

Ayudar a desarrolladores a entender rápidamente:

- Qué hace cada carpeta.
- Qué interfaces son estables (para no romperlas).
- Dónde agregar nuevos providers o cambiar la infraestructura.

## Vista general

El repositorio es un monolito liviano con dos áreas:

- `webapp/`: API REST + UI mínima (FastAPI + Jinja + WebSocket).
- `price_monitor/`: lógica de dominio (scraping, parseo, construcción de filas, selección) y CLI.

## Componentes y responsabilidades

### Dominio (`price_monitor/`)

- `providers/`: adaptadores por plataforma (ej. Airbnb). Deben exponer funciones que devuelvan calendario y precios en un formato uniforme.
- `core/`: helpers puros (calendario, construcción de rows, utilidades CSV/JSON, selección).
- `cli/`: orquestación desde línea de comandos (flags -> ejecución -> archivos resultado).

Contrato esencial (ejemplo simplificado):
`fetch_calendar(session: requests.Session, listing_id: str, start: date, end: date, guests: int, **opts) -> CalendarData`
`CalendarData` es serializable y contiene `{date, price, available, currency, guests}`.

### Web (`webapp/`)

- `main.py`: arranque de FastAPI, endpoints REST y WebSocket.
- `crud.py`: operaciones transaccionales sobre la base de datos (crear job, guardar resultados, exportar snapshot).
- `models.py` / `schemas.py`: entidades persistentes (SQLAlchemy) y DTOs (Pydantic).
- `templates/` + `static/`: UI mínima para lanzar scrapes y ver progreso.

### Persistencia

Implementación actual: SQLite con SQLAlchemy. Entidades clave:

- `Listing`: metadata del anuncio.
- `PriceRecord`: precio + disponibilidad por fecha.
- `ScrapeJob`: estado y progreso del proceso de scraping.
- `Workspace` / `Season`: agrupaciones lógicas para segmentar scrapes.

### CLI

Flags principales soportadas (ver código para lista completa): `--start`, `--end`, `--guests`, `--currency`, `--locale`, `--delay`, `--retries`, `--max-workers`, `--output-dir`, `--json`.

## Flujo de un `ScrapeJob`

1. Creación: UI o CLI registra job (`estado=queued`).
2. Ejecución: tarea en background llama a provider(s), transforma a `PriceRecord` y actualiza progreso.
3. Seguimiento: WebSocket (`/ws/scrape-jobs/{job_id}`) emite eventos periódicos leyendo estado en DB (polling simple cada ~500 ms).
4. Finalización: estado `succeeded` o `failed`; registros persistidos y posible export a CSV.

## Interfaces clave

Provider:

- Input: `session`, `listing_id`, `start`, `end`, `guests`, `locale`, `currency`.
- Output: iterable de `{date, price, available, currency}`.
- Errores: excepciones específicas para diferenciar casos (rate-limit, not-found, etc.).

CRUD / DB (contrato estable):

- `create_scrape_job(params) -> job_id`.
- `run_scrape_job(job_id) -> None`.
- `get_price_records(listing_id, start, end) -> list[PriceRecord]`.

WebSocket:

- Mensajes: `{type: 'progress'|'event'|'log', job_id, payload}`.

## Operaciones y observabilidad

- Logging estructurado (`webapp/logging_config.py`).
- Sin métricas aún: sugerido agregar `/health` y métricas Prometheus.
- Reintentos: controlados por parámetro `--retries` en CLI / configuración del job.

## Extensión y evolución (principales próximos pasos técnicos sugeridos)

- Integrar cola/broker (Redis/Celery/RQ) para desacoplar workers.
- Sustituir polling por eventos push (pub/sub).
- Migraciones formales (Alembic) y Postgres para entornos productivos.
- Métricas y health-check.

## Despliegue (resumen)

Desarrollo local: crear `.venv`, instalar dependencias y ejecutar `python run_webapp.py` (ver README para comandos exactos). Para producción ligera: Uvicorn/Gunicorn detrás de Nginx + base de datos gestionada.

## Referencias cruzadas

- Visión de producto: `VISION.md`.
- Estado y roadmap técnico: `PROJECT_STATUS.md`.
- Uso práctico y comandos: `README.md`.

---

Este archivo es la fuente única de verdad sobre arquitectura técnica. Cambios significativos deben actualizarse aquí y referenciarse desde el README en lugar de duplicarse.
