# Estado del proyecto — Price Monitor (técnico)

Fecha: 2025-11-09

Este documento resume el estado actual y el roadmap cercano. Para arquitectura ver `ARCHITECTURE.md`. Para la visión de producto ver `VISION.md`.

## Qué funciona hoy

- CLI (`price_monitor/cli/main.py`) para ejecutar scrapes por rango de fechas y exportar CSV/JSON.
- Webapp (FastAPI) con páginas simples (Jinja) y API REST para crear jobs, consultar estado y exportar snapshots.
- Persistencia con SQLAlchemy sobre SQLite: `Listing`, `PriceRecord`, `ScrapeJob`, `Workspace`, `Season`.
- WebSocket `/ws/scrape-jobs/{job_id}` con actualizaciones periódicas de progreso (polling interno ~500 ms).
- Suite de tests unitarios e integración.

## Endpoints relevantes (resumen)

- POST `/api/workspaces` — crear workspace
- GET `/api/workspaces` — listar workspaces
- POST `/api/workspaces/{id}/seasons` — crear season
- POST `/api/seasons/{season_id}/scrape` — lanzar scrapes para una season
- GET `/api/scrape-jobs/{job_id}` — consultar job
- GET `/api/prices/{listing_id}` — obtener precios por listing y rango
- GET `/api/seasons/{season_id}/snapshots` — exportar snapshots CSV

## Limitaciones actuales

- Solo hay un provider implementado (Airbnb).
- Los jobs corren en `BackgroundTasks` (no hay cola/broker externo).
- WebSocket con polling desde el servidor (no push directo del worker).
- Sin migraciones formales (Alembic) ni soporte Postgres listo para producción.

## Próximos pasos prioritarios (técnicos)

1. Introducir migraciones con Alembic y preparar compatibilidad con Postgres.
2. Desacoplar ejecución de jobs usando un broker (Redis/Celery o RQ).
3. Agregar endpoint `/health` y métricas (Prometheus) para observabilidad.
4. Definir excepciones específicas de provider y política de reintentos uniforme.
5. Documentar contrato del provider en `ARCHITECTURE.md` (mantener SSOT, sin duplicar aquí).

## Notas para desarrolladores

- Mantener `price_monitor/core` como capa compartida entre CLI y webapp.
- No romper contratos estables: `crud.create_scrape_job`, `crud.run_scrape_job`, esquemas de `schemas.py`.
