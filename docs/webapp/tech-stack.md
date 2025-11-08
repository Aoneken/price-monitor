# Tech stack propuesto (MVP y escalamiento)

Fecha: 2025-11-08

## objetivos del stack

- Local-first, simple de instalar y correr.
- Reutilizar la librería de scraping existente.
- Crecer hacia múltiples proveedores (Airbnb hoy; Booking/Expedia mañana).
- Progreso en tiempo real y persistencia confiable.

## backend

- Framework: FastAPI (rápido, tipado, docs automáticas, fácil de montar localmente).
- Server: Uvicorn (ASGI) con reload en dev.
- Serialización/validación: Pydantic (modelos de request/response, settings).
- Concurrencia de scraping: ThreadPoolExecutor (límites estrictos), manteniendo lógica pura en módulo `price_monitor.core`.
- WebSocket para progreso por job (emisión de eventos desde worker -> cliente).
- Logging: `logging` estándar + formato estructurado (JSON) opcional.

## base de datos

- Desarrollo: SQLite (archivo local, cero fricción).
- Producción local avanzada / multiusuario: PostgreSQL.
- ORM/Migraciones: SQLAlchemy 2.x + Alembic.
- Config: variables de entorno (`.env` + Pydantic Settings).

## frontend

- MVP rápido: Server-side templates (Jinja2) + HTMX/Alpine para interacciones ligeras.
- Alternativa posterior: React + Vite si la UI crece.
- Estilos: Tailwind CSS o CSS sencillo (MVP); mantener bajo costo cognitivo.

## tareas y colas

- MVP: workers en el mismo proceso (ThreadPool) con límites por job y globales.
- Escalable: separar proceso de workers (uvicorn + proceso worker) o Celery/RQ si fuese necesario.

## empaquetado y tooling

- Python 3.10+.
- Dependencias: `requests`, `rich` (CLI), `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `python-dotenv`.
- Testing: `pytest`.
- Lint/format: `flake8`, `black`, `isort` (opcional); mantener reglas simples.

## seguridad

- Alcance local; sin usuarios externos inicialmente.
- CSRF si se usan formularios; CORS solo si hay separación FE/BE.
- Rate limiting y backoff en providers; validación de parámetros de scraping.

## observabilidad

- Métricas a nivel job (duración, peticiones, retries, % días con precio).
- Logs de eventos de progreso para depurar.

## por qué este stack

- Minimiza complejidad inicial y permite migrar a arquitectura más robusta sin reescribir la lógica (separada en `price_monitor`).
- Ecosistema Python consistente con el scraping actual.
