# TESTING & CALIDAD V3

## 1. Objetivo
Asegurar confiabilidad, prevenir regresiones y cuantificar calidad de extracción y datos.

## 2. Pirámide de Tests
| Nivel | Descripción | Herramienta |
|-------|-------------|------------|
| Unitario | Funciones puras (normalización, validación) | pytest |
| Contrato | Robots, repositorios, normalizador | pytest + fixtures |
| Integración | Event bus + persistencia + robots simulados | docker-compose + pytest |
| E2E | Flujo completo tarea a dashboard | script + entorno staging |
| Performance | Concurrencia 100+ URLs | locust / custom harness |

## 3. Suites Propuestas
- `tests/unit/`: validadores, FX provider mock.  
- `tests/contract/`: `test_robot_contract.py`, `test_repository_contract.py`.  
- `tests/integration/`: `test_event_flow.py`.  
- `tests/e2e/`: `test_full_pipeline.py`.  
- `tests/selectors/`: smoke selectores (chequea existencia mínima).  

## 4. Mocking Selectores
Generar HTML synthetic con estructuras múltiples para validar extractor robusto sin depender de sitios reales.

## 5. Métricas de Calidad
| Métrica | Objetivo |
|---------|----------|
| Cobertura líneas | > 70% inicial |
| Falsos precios | < 1% |
| Fallos extractor por release | Tendencia decreciente |
| Tiempo medio pipeline | < 5s end-to-end |

## 6. Detección de Regresiones Selectores
Job diario: ejecutar smoke sobre URLs de prueba; si falla > 30% → alerta `SelectorRegressionDetected`.

## 7. Análisis Estático
- `ruff` / `flake8` para estilo y errores.  
- `mypy` para tipos en módulos críticos.  

## 8. Ejemplo Test Contrato Robot
```python
def test_robot_fetch_contract(airbnb_robot, listing_ctx):
    raw = airbnb_robot.fetch(listing_ctx, date.today()+timedelta(days=5))
    assert isinstance(raw.precio_total, float)
    assert raw.noches_consultadas in (1,2,3)
    assert raw.moneda in ('USD','EUR')
```

## 9. Performance Harness (Pseudo)
```python
async def run_load(urls):
    sem = asyncio.Semaphore(10)
    async def task(url):
        async with sem:
            return await robot.fetch_async(url)
    return await asyncio.gather(*[task(u) for u in urls])
```

## 10. Data Quality Checks
- Precios nulos inesperados.  
- Outliers extremos.  
- Moneda desconocida.  
- Duplicados por (listing, fecha_noche).  

## 11. Reporte Diario
Generar `quality_report.json`: total_observations, anomalies_detected, blocked_events, avg_duration_ms.

## 12. CICD (Futuro)
Pipeline: lint → tests unit/contract → build docs → integration (docker) → generar artefacto.  

---
Fin del documento testing y calidad V3.
