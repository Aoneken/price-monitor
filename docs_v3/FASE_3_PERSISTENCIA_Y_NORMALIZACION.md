# Fase 3 – Persistencia y Normalización

## Objetivo
Persistir eventos/observaciones y normalizar precios con validadores y moneda.

## Alcance
- Tablas: `raw_observations`, `normalized_observations`, `scrape_events`.
- Normalización: currency FX, validación de rango, calidad de dato.
- Repositorios y queries para analítica básica.

## Criterios de aceptación
- Pipeline raw→normalized reproducible.
- Rechazo de outliers con trazabilidad (evento PriceRejected).
- Consultas por fecha/plataforma/establecimiento.

## Lecciones heredadas relevantes
- Rango razonable y auditoría de rechazos.
- Linaje de datos para re-procesamiento.
