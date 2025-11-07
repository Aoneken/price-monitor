# ARQUITECTURA V3 – Diseño de Sistema

## 1. Objetivo
Proveer un blueprint técnico preciso para implementar la nueva versión desacoplada, escalable y observable.

## 2. Vista 4+1
- Casos de uso: Ingestar precios multi-fuente, consultar históricos, generar análisis comparativos.  
- Vista lógica: Módulos dominantes (Dominio, Ingesta, Eventos, Persistencia, Analítica, Presentación, Observabilidad).  
- Vista desarrollo: Paquetes y repositorio con estructura clara.  
- Vista procesos: Flujos asíncronos y colas.  
- Vista física: Contenedores (Docker) y despliegue escalable futuro.  

## 3. Diagrama Lógico (Texto)
```
[UI/REST/API] --> [Servicio Dominio] --> [Event Bus] --> [Workers Ingesta]
                                    \-> [Persistencia]
[Workers Ingesta] --> (Emiten eventos PriceCollected) --> [Persistencia]
[Persistencia] <--> [Consulta / Analítica] --> [UI Dashboard]
[Observabilidad] (Logs, Métricas, Trazas) conectada transversalmente
```

## 4. Componentes Principales
| Componente | Responsabilidad | Tecnologia | Nota |
|------------|-----------------|-----------|------|
| api_gateway (futuro) | Exponer endpoints REST | FastAPI | Permite integraciones externas |
| ui_app | Interfaz interactiva | Streamlit (fase transición) | Separar vista vs lógica |
| domain_core | Entidades y servicios | Python | Sin dependencias infra |
| events_bus | Publicar/Consumir mensajes | Redis Streams / NATS / RabbitMQ | Elección según disponibilidad |
| ingestion_workers | Ejecutar robots + adaptadores API | Python asyncio | Escalable horizontal |
| persistence | Repositorios y mapeo | SQLite→Postgres | Patrón Repository |
| analytics_engine | Agregaciones, métricas | SQL / Pandas / futuro Spark | Desacoplado del core |
| observability | Logs, métricas, tracing | Logging estructurado + Prometheus | Dashboard Grafana |

## 5. Flujos Clave
### 5.1 Solicitud de Monitoreo
1. Usuario crea tarea (UI / API).  
2. Servicio Dominio valida parámetros y emite `PriceQueryRequested`.  
3. Worker Ingesta consume evento y prepara sub-tareas por plataforma.  
4. Robots ejecutan extracción.  
5. Cada resultado emite `PriceCollected`.  
6. Persistencia guarda y emite `PriceStored`.  
7. UI se actualiza vía polling o websocket (futuro).  

### 5.2 Actualización de Selectores
1. Admin sube JSON nuevo.  
2. Servicio Selectores versiona y valida integridad.  
3. Emite `SelectorsUpdated`.  
4. Robots activos recargan configuración en próximo ciclo.  

### 5.3 Manejo de Bloqueo
1. Robot detecta bloqueo → emite `RobotBlocked`.  
2. Motor de mitigación ajusta delay / rota IP / marca escalado.  
3. Si excede umbral → `PlatformEscalation` para alerta manual.  

## 6. Estratégias Técnicas
| Área | Estrategia |
|------|------------|
| Concurrencia | `asyncio` + lotes por plataforma para minimizar sesiones navegador |
| Resiliencia | Retries + fallback DOM/API + circuit breaker (estado de salud robot) |
| Escalabilidad | Separación workers en contenedores; filas por plataforma |
| Configuración | `config/` + variables de entorno + archivo selectors versionado |
| Seguridad | Secretos en `.env` fuera de Git, validar origen de datos API |
| Observabilidad | Logging JSON; métricas (tiempo extracción, errores, reintentos) |

## 7. Mapa de Paquetes (Propuesto)
```
price-monitor/
  app/                 # Streamlit transicional
  api/                 # (Futuro) FastAPI
  domain/
    models/
    services/
    events_types.py
  events/
    bus.py
    publishers.py
    consumers/
  ingestion/
    robots/
      base.py
      booking.py
      airbnb.py
      expedia.py
    adapters/
      api_booking.py
      manual_import.py
    selector_loader.py
  persistence/
    repositories/
    mappers/
    migrations/
  analytics/
    queries/
    aggregations/
    forecasting/
  config/
  observability/
    logging.py
    metrics.py
  tests/
    unit/
    integration/
    contract/
    e2e/
  docs_v3/
```

## 8. Decisiones Arquitectónicas (ADR Resumidos)
| ID | Decisión | Status | Justificación | Alternativas |
|----|----------|--------|---------------|--------------|
| ADR-01 | Event Bus | Aceptada | Desacoplar scraping y UI | Llamadas directas |
| ADR-02 | Repositorios | Aceptada | Abstraer BD y facilitar migración | ORM directo everywhere |
| ADR-03 | Robots con SDK | Aceptada | Facilitar incorporación tercera plataforma | Clases adhoc sin contrato |
| ADR-04 | Persistencia incremental | Aceptada | No bloquear escritura mientras se analiza | Escritura sin colas |
| ADR-05 | Moneda normalizada | Aceptada | Comparación multi-mercado | Almacenar solo bruto |

## 9. Escenarios de Carga y Rendimiento
Prueba objetivo: 1000 URLs / 4 plataformas / ventana 30 días.  
- Estrategia: particionar tareas en lotes de 50 URLs, concurrency 10 navegadores.  
- Métrica clave: Tiempo medio extracción < 2.5s/URL; error rate < 5%.  

## 10. Plan de Migración Técnica
Fases en detalle en `MIGRACION_V1_A_V3.md`.

## 11. Observabilidad
Campos log: timestamp, level, robot_name, event_type, establecimiento_id, plataforma, duration_ms, success, error_code.  
Métricas Prometheus: `scrape_duration_seconds`, `scrape_errors_total`, `robot_block_events_total`, `price_collected_total`.

## 12. Integraciones Futuras
- API externas (Channel Managers) → adaptadores en `ingestion/adapters`.  
- ML Forecasting → `analytics/forecasting/model_runner.py`.  

## 13. Seguridad Básica
Separación de credenciales; sanitización de logs (no imprimir URLs con tokens).  

---
Fin del documento de arquitectura V3.
