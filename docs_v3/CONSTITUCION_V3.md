# CONSTITUCIÓN V3 – Price Monitor

## 1. Propósito Supremo
Establecer los principios, límites, derechos y deberes que rigen la tercera versión (V3) de la plataforma Price Monitor para garantizar: escalabilidad, mantenibilidad, auditabilidad, resiliencia ante cambios externos (selectores, plataformas, anti-bot), rapidez de incorporación de nuevas fuentes de datos y capacidad de evolución hacia análisis avanzado y automatización.

## 2. Visión
Transformar el actual MVP centrado en scraping directo + dashboard simple en un sistema de inteligencia de precios modular, extensible y orientado a eventos que permita operar con múltiples proveedores de datos (scraping, APIs comerciales, cargas manuales, integraciones PMS) y escalar a recomendaciones con ML/AI.

## 3. Alcance Constitucional
Esta constitución define el marco conceptual, arquitectónico y operativo. El código existente se puede refactorizar o reemplazar excepto:
- Conservación conceptual y lógica de la tabla `Establecimientos` (núcleo del dominio).
- Conservación semántica de la "búsqueda de precios por noche" y la inferencia de ocupación.
Todo lo demás es susceptible de rediseño.

## 4. Principios Filosóficos
1. Dominio primero: Las decisiones técnicas sirven al modelo de negocio (monitorizar variaciones de precio y disponibilidad).  
2. Evolución incremental: Cada módulo debe poder desplegarse y medirse aislado.  
3. Extensibilidad explícita: Cualquier nueva plataforma se añade sin tocar el núcleo (Open/Closed).  
4. Observabilidad por defecto: Ningún proceso crítico sin logs estructurados, métricas y trazas mínimas.  
5. Deuda técnica registrada: Cada compromiso temporal debe tener ticket.  
6. Falla segura: Un error de robot jamás bloquea el pipeline completo.  
7. Privacidad y cumplimiento: Datos sensibles (credenciales, tokens API) fuera del repo y gestionados por vault / variables de entorno.  
8. Anti-fragilidad: Se espera rotura de selectores; el sistema prepara mecanismos para actualización remota y fallback.  
9. Transparencia de datos: Cada dato almacenado debe tener su linaje (origen, timestamp, método).  
10. Reproducibilidad: Cualquier precio puede regenerarse (o explicar por qué no) a partir de eventos y configuraciones.  
11. Memoria histórica: Los errores y diagnósticos previos (V1/V2) se preservan explícitamente para evitar regresiones (ver `LECCIONES_ERRORES_V1_V2.md`).

## 5. Objetivos Estratégicos V3
- Separar scraping, persistencia y analítica en capas desacopladas.  
- Introducir un Bus de Eventos para orquestar tareas y permitir múltiples productores (scrapers, importadores).  
- Migrar de enfoque sincrónico monolítico a procesamiento distribuido (opcional contenedores).  
- Diseñar modelo de datos orientado a histórico y comparaciones multi-dimensión.  
- Añadir soporte agnóstico para monedas y normalización de tasas.  
- Establecer política de versionamiento semántico y tagging retroactivo de v1.x.  
- Definir contrato formal para robots (SDK interno).  
- Especificar estrategia de pruebas (unitarias, contrato, integración, regresión selectores, smoke E2E).  
- Preparar migración futura a Postgres + opcional time-series (Timescale) para escalamiento.  

## 6. No Funcionales Clave
| Categoría | Objetivo | Métrica Base | Meta V3 |
|-----------|----------|--------------|---------|
| Rendimiento | Scrape concurrente | URLs / minuto | >= 30 (headless)
| Resiliencia | Fallos de selector | % recuperación por fallback | >= 70% sin intervención
| Trazabilidad | Linaje de dato | Campos mínimos | origen, método, robot_version, hash_html
| Mantenibilidad | Creación nuevo robot | Tiempo | < 2h sin tocar núcleo
| Confiabilidad | Falsos precios | % sobre total | < 1% (con validadores)
| Seguridad | Exposición credenciales | Incidentes | 0

## 7. Mapa Macro Modular
1. Capa Dominio (Modelo + Servicios).  
2. Capa Ingesta (Robots, Adaptadores API, Import Manual).  
3. Event Bus (mensajes: PriceQueryRequested, PriceCollected, SelectorFailed, RobotHealth).  
4. Capa Persistencia (Repositories + Query Layer).  
5. Capa Analítica (Agregaciones, indicadores, feature store futuro).  
6. Capa Presentación (UI web / API REST / CLI).  
7. Capa Observabilidad (Logging estructurado, métricas Prometheus, dashboards Grafana).  

## 8. Derechos y Obligaciones de un Robot
Derechos:  
- Recibir contexto de tarea con parámetros estándar (establecimiento_id, plataforma, fechas, currency_preference).  
- Acceder a librerías comunes (stealth, retry, selector loader).  
Obligaciones:  
- Retornar un objeto ResultadoRobot con campos normalizados.  
- Implementar detección de bloqueo y emitir evento.  
- No lanzar excepciones sin capturar; encapsularlas en error_code / error_message.  
- Reportar versión propia (robot_version semantic).  

## 9. Políticas de Datos
- Un precio final se deriva de: fuente (scrape / api / manual), moneda original, normalización, fecha_noche, fecha_ingesta, calidad (score).  
- Ocupación inferida se separa en campo calculado; no sobrescribe precio.  
- No eliminación física salvo proceso de purga con retención definida (por defecto 18 meses).  

## 10. Versionamiento Retroactivo Propuesto
- v1.0: Implementación MVP (commit 8d63375).  
- v1.1: Configuración, tests básicos, documentación inicial (hasta commit 89004ad).  
- v1.2: Mejoras scraping + soporte Expedia (commit da7e904).  
- v1.3: Sistema eliminación datos + batch establecimientos (commits 8c89ab3, 7aaf00f).  
- v1.3.1: Fix session state (commit 79c8b0b).  
- v3.0 (planeado): Constitución y refactor estructural (esta rama).  

## 11. Riesgos Identificados
| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Cambios agresivos en DOM | Pérdida extracción | Estrategias multi-fuente + heurística regex + API fallback |
| Bloqueos masivos anti-bot | Interrupción de ingesta | Rotación IP / Proxy pool / Scheduler adaptativo |
| Escalamiento de volumen | Latencia consultas | Índices + partición temporal + migración Postgres |
| Datos inconsistentes multi-fuente | Métricas erróneas | Normalizador + reconciliación + reglas de validación |
| Deuda técnica orquestador | Dificultad mantenimiento | Reescritura a architecture event-driven + servicios separados |

## 12. Mandatos para la Implementación
1. Crear SDK interno `pm_robots` con clase `AbstractRobotV3`.  
2. Introducir capa `events/` con publicadores y consumidores.  
3. Rediseñar base de datos (ver DATOS_BD_V3.md).  
4. Extraer lógica de validación de precio a `pricing/validators.py`.  
5. Añadir pruebas de carga mínima para 100 URLs concurrentes (mock).  
6. Etiquetar versiones v1.x con tags Git.  
7. Publicar documentación generada en `docs_v3/` y enlazar desde README.  

## 13. Cláusula de Cambio
Cualquier modificación a esta constitución requiere:  
- Justificación escrita (issue)  
- Aprobación >1 revisor técnico  
- Tag de versión menor (v3.x) si no cambia modelo de datos; mayor si lo altera.  

## 14. Entrada en Vigencia
Se considera activa al merge de la rama de implementación V3 en `main` y creación de tag `v3.0.0`. Documentos complementarios obligatorios: `ARQUITECTURA_V3.md`, `DATOS_BD_V3.md`, `LECCIONES_ERRORES_V1_V2.md`.

---
Fin del documento constitucional V3.
