# Fase 1 – Datos y Dominio

## Objetivo
Definir el modelo de dominio y los datos mínimos viables para soportar ingesta, normalización y análisis.

## Alcance
- Entidad: Establecimiento (invariantes).
- Observaciones: Raw vs Normalized.
- Reglas: ocupación inferida, validación de precios.

## Contratos (inputs/outputs)
- Input: PriceQuery (establecimiento, plataforma, fechas, moneda).
- Output RawObservation: {source, html/json/raw, ts, metadata}.
- Output NormalizedObservation: {price, currency, date, quality, lineage}.

## Criterios de aceptación
- Esquema mínimo activo (Establecimientos).
- Diseño de tablas raw/normalized propuesto.
- Políticas de validación definidas.

## Lecciones heredadas relevantes
- Separar datos brutos de procesados (evita recalcular scraping).
- Expandir multi-noche a observaciones por noche.
