# Propuesta de estructura del repositorio (evolución)

Fecha: 2025-11-08

## estado actual (simplificado)

```
price-monitor/
  tests/ (antes Foco_01/... movido)
    Foco_01/Temp-25-26/tests/airbnb/prototype.v2/scrape_real_prices.py
    ... otros scripts y artefactos
  docs/webapp/price-monitor-webapp-spec.md
  requirements.txt
```

Scripts acoplados (funciones mezcladas) y salidas CSV en carpetas de pruebas.

## objetivos de reorganización

- Separar lógica de scraping en paquete reutilizable (`price_monitor/`).
- Mantener CLI estable para backward compatibility.
- Preparar base para backend FastAPI y posterior frontend.
- Añadir espacio claro para tests unitarios y de integración.

## estructura propuesta (fase 1)

```
price-monitor/
  price_monitor/
    core/
      calendar.py
      pricing.py
      rows.py
      io_csv.py
      models.py
      selection.py
    providers/
      airbnb.py
      booking.py        (placeholder)
      expedia.py        (placeholder)
    cli/
      __init__.py
      main.py           (argparse/click con subcomandos: scrape, list, batch)
    config.py
    logging.py
  tests/
    unit/
      test_calendar.py
      test_rows.py
      test_selection.py
    integration/
      test_airbnb_scrape.py
    data-fixtures/
      establecimientos.csv (copias controladas)
  scripts/
    scrape_real_prices.py  (shim que llama a price_monitor.cli.main)
  output/                 (resultados por defecto de la CLI)
  docs/
    webapp/
      price-monitor-webapp-spec.md
      tech-stack.md
      repo-structure.md
  requirements.txt
  README.md
```

## estructura propuesta (fase 2, web app)

```
price-monitor/
  app/
    api/
      routers/
        workspaces.py
        seasons.py
        establishments.py
        scrape_jobs.py
      deps.py
    services/
      scrape_runner.py
      summary.py
    websocket/
      progress.py
    main.py (FastAPI app)
  price_monitor/ (igual que fase 1)
  frontend/ (si se elige React/Vite) o templates/ + static/
```

## migración incremental

1. Extraer funciones puras de `scrape_real_prices.py` a `price_monitor/core` y `providers/airbnb.py`.
2. Crear `price_monitor/cli/main.py` con subcomando `scrape-airbnb` que reusa esas funciones.
3. Reemplazar contenido de `scripts/scrape_real_prices.py` para delegar en CLI.
4. Añadir tests unitarios (calendar, min_stay, rows) y un test de integración (scrape corto de un listing).
5. Actualizar `README.md` con nueva forma de invocar.
6. Fase 2: agregar FastAPI backend usando el paquete ya modularizado.

## naming y convenciones

- Módulos snake_case, clases PascalCase, funciones/variables snake_case.
- Directorios en singular para dominio (`core`, `providers`).
- Tests: `test_*.py` y usar fixtures en `data-fixtures`.

## control de parámetros

- Config centralizada (`config.py`) con Pydantic (valores por defecto, límites de concurrencia, retries máximos).
- Subcomandos override (flags CLI) y en backend se puede leer de ENV/DB.

## manejo de salidas

- Por defecto `output/` para CLI. Backend guardará en DB y exportará sólo bajo demanda (CSV/JSON).
- Evitar mezclar resultados persistentes con fixtures de tests.

## validación final

- Mantener script viejo como shim hasta confirmar adopción de CLI nueva.
- Documentar diferencias en `README.md` sección “Migración”.
