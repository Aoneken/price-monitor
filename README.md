# Price Monitor

Aplicación local para monitorear precios y disponibilidad de alojamientos (inicialmente Airbnb) y generar reportes reproducibles. Incluye una **webapp** ligera (FastAPI + Jinja) y una **CLI** que comparten el mismo core de scraping.

> Para detalles de arquitectura ver `ARCHITECTURE.md`. Para visión de producto ver `VISION.md`. Para estado técnico y roadmap ver `PROJECT_STATUS.md`.

## Características principales

- Scraping de calendario y precios por rango de fechas y cantidad de huéspedes.
- Exportación a CSV y JSON (desde CLI y webapp).
- Seguimiento de progreso en tiempo real vía WebSocket.
- Agrupación de listados mediante _workspaces_ y _seasons_.
- Datos locales y reproducibles (SQLite por defecto).

## Requisitos

- Python 3.10+
- Opcional: `make` para usar atajos (ver `Makefile`).

## Instalación rápida

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para instalar dependencias de desarrollo (lint, tests):

```bash
pip install -r requirements-dev.txt
```

También podés usar las _tasks_ de VS Code definidas en `.vscode/tasks.json`:

- `setup: Create Virtual Environment`
- `setup: Install Dependencies`
- `setup: Install Dev Dependencies`

## Ejecutar la webapp

```bash
python run_webapp.py
```

Luego abrir el navegador en `http://localhost:8000`.

## Uso de la CLI

La CLI principal está en `price_monitor/cli/main.py`.

Ejemplo básico:

```bash
python -m price_monitor.cli.main \
  --start 2025-12-01 \
  --end 2025-12-10 \
  --guests 2 \
  --output-dir data/output
```

Flags comunes:

- `--start YYYY-MM-DD` / `--end YYYY-MM-DD`
- `--guests <int>`
- `--currency <ISO>`
- `--locale <locale>`
- `--delay <segundos>` (entre requests)
- `--retries <int>`
- `--max-workers <int>`
- `--output-dir <path>`
- `--json` (export también a JSON)

## Tests

Ejecutar todos los tests:

```bash
python -m pytest tests -v
```

O usar la task `test: All`.

Cobertura:

```bash
python -m pytest tests --cov=price_monitor --cov=webapp --cov-report=term-missing --cov-report=html
```

## Lint y formato

```bash
python -m flake8 price_monitor webapp tests
python -m mypy price_monitor webapp --ignore-missing-imports
python -m isort price_monitor webapp tests scripts
python -m black price_monitor webapp tests scripts
```

Task combinada: `format: All` y `check: All`.

## Estructura del repositorio (resumen)

```text
price_monitor/   # Lógica de dominio y CLI
webapp/          # FastAPI + UI mínima + CRUD y modelos
run_webapp.py    # Entry point para la webapp
ARCHITECTURE.md  # Contratos y organización técnica
VISION.md        # Propósito y principios de producto
PROJECT_STATUS.md# Estado actual y roadmap cercano
```

## Flujo resumido de un scrape

1. Crear job (CLI o API).
2. Ejecutar scraping (BackgroundTask): obtiene calendario del provider y genera `PriceRecord`.
3. Progreso visible por WebSocket.
4. Exportación (CSV/JSON) y consulta vía API.

## Extensión: agregar un nuevo provider

1. Crear módulo en `price_monitor/providers/`.
2. Implementar función `fetch_calendar(...)` retornando estructura uniforme.
3. Manejar excepciones específicas (rate limit, not found, etc.).
4. Integrar en orquestación (CLI / CRUD) según corresponda.
5. Agregar tests de integración y actualizar referencias si cambia contrato.

## Roadmap breve (ver detalles en `PROJECT_STATUS.md`)

- Migraciones Alembic + soporte Postgres.
- Cola de jobs (Redis/Celery o RQ) para desacoplar ejecución.
- Métricas y endpoint `/health`.
- Más providers (Booking, etc.).

## Principio SSOT

Información conceptual: `VISION.md`.
Contratos técnicos y arquitectura: `ARCHITECTURE.md`.
Estado y próximos pasos: `PROJECT_STATUS.md`.
README se limita a uso y onboarding. Cambios sustanciales deben centrarse en actualizar la fuente correspondiente y referenciarla aquí.

## Licencia

(Agregar aquí si se define una licencia pública. Actualmente uso interno.)

---

Documentación generada y alineada con principios de simplicidad y no duplicación. Cualquier mejora estructural debe reflejarse primero en `ARCHITECTURE.md`.
