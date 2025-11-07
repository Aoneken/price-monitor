# ROADMAP V3 – Fases y Entregables

## 1. Estrategia General
Construcción incremental con validación temprana, priorizando desacoplamiento y observabilidad antes de funcionalidades avanzadas.

## 2. Fases
| Fase | Objetivo | Entregables | Criterio de Done |
|------|----------|-------------|------------------|
| S1 | Fundamentos | Constitución, Arquitectura, Dominio, BD (esquema) | Documentos aprobados + tags v1.x creados |
| S2 | Event Bus | Módulo eventos + publishers + consumidores base | Eventos PriceQueryRequested y PriceCollected funcionales |
| S3 | Refactor Robots | SDK robots + migración Booking/Airbnb/Expedia | Robots operando vía bus, métricas básicas |
| S4 | Persistencia Nueva | Repositorios Postgres + migración datos | Consultas equivalentes a versión anterior |
| S5 | Normalización FX | Tabla fx_rates + servicio normalizador | Precios normalizados disponibles en Dashboard |
| S6 | Observabilidad | Logging JSON + métricas Prometheus + tablero | KPIs visibles y alertas bloqueos |
| S7 | UI Evolución | Refactor componentes + página eventos | Reducción tiempo feedback < 1s |
| S8 | Calidad & Testing | Tests contrato + smoke selectores + carga | Cobertura > 70%, reporte performance |
| S9 | Anomalías & Calidad | Motor detección outliers + score | Eventos PriceAnomalyDetected generados |
| S10 | Preparación ML | Feature store inicial + vistas agregadas | Dataset entrenable disponible |
| S11 | API Pública | Endpoints CRUD + precios agregados | Documentación OpenAPI publicada |
| S12 | Lanzamiento v3.0 | Tag v3.0.0 + guía migración | E2E ok + comparativa métricas v1 vs v3 |

## 3. Métricas de Progreso
| Métrica | Método |
|---------|--------|
| % Fases completadas | Conteo Done / Total |
| Error rate scraping | Promedio últimos 7 días |
| Tiempo medio ingesta | Duración promedio PriceCollected |
| Selectores rotos (24h) | Conteo SELECTOR_NOT_FOUND |

## 4. Dependencias Externas
- Postgres provisioning.  
- Redis / RabbitMQ para bus.  
- Servicio FX (fixer.io, exchangerate.host).  

## 5. Riesgos por Fase
| Fase | Riesgo | Mitigación |
|------|--------|------------|
| S2 | Complejidad eventos | Empezar con Redis Streams simple |
| S4 | Migración datos | Ensayo en entorno staging + verificación diff |
| S6 | Métricas incompletas | Implementar primero logging estructurado |
| S9 | Falsos positivos | Ajustar score con ventana histórica |

## 6. Checklist Pre-Release v3.0
- [ ] Tags v1.x creados.  
- [ ] Migración datos validada (conteo, integridad).  
- [ ] Pruebas E2E nuevas pasan.  
- [ ] Métricas bloqueo < umbral definido.  
- [ ] Documentación completa en `docs_v3/`.  
- [ ] README actualizado con enlace a constitución.  

## 7. Mantenimiento Post v3.0
- Ciclo mensual de revisión selectores.  
- Re-entrenamiento detección anomalías trimestral.  
- Auditoría seguridad semestral.  

---
Fin del documento roadmap V3.
