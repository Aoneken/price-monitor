# Fase 4 – Observabilidad y Testing

## Objetivo
Asegurar visibilidad y calidad del sistema con logs, métricas y pruebas por capas.

## Alcance
- Logs estructurados, métricas (Prometheus), dashboards.
- Testing: unit (extractor/validador), integración (pipeline), contrato (robots), E2E.
- Health-check de selectores y tasa de éxito.

## Criterios de aceptación
- Dashboard con métricas clave.
- Suite de tests mínima verde (unit/integration/contract).
- Alertas por caída de health de selectores.

## Lecciones heredadas relevantes
- Falta de granularidad de fallos → taxonomía y métricas.
- Evitar enfocarse solo en E2E; cubrir capas internas.
