# Metodología de Extracción – Expedia (V3 Definitiva)

Fecha: 2025-11-07 (actualizada con relevamiento manual)

## Objetivo
Extraer de forma reproducible:
- Precio total efectivo (post-descuento) y precio por noche
- Precio original (tachado) si hay descuento
- Monto de descuento y porcentaje derivado
- WiFi incluido (Sí/No)
- Desayuno incluido (Sí/No)
- Fecha de referencia (check-in)

## Consideraciones específicas
Expedia muestra un panel sticky con: precio por noche, total, badge de descuento (ej. `$56 de dto.`) y precio original tachado. El DOM es la fuente más directa cuando se renderiza; puede requerir scroll e interacción mínima. Limpieza se descarta como dato en V3.

## Estrategia Multicapa
1. DOM sticky pricing card (precio por noche, total, descuento, precio original) – fuente principal.
2. XHR/API (rates/availability) – validación cruzada y respaldo.
3. JSON embebido – respaldo adicional.
4. Regex – último recurso.

## Flujo operativo
1. Navegar usando `chkin/chkout` y variante `checkIn/checkOut` con ocupación (adults/children, currency).
2. Verificar fechas en botones (`data-testid="uitk-date-selector-input1-default"`). Si difieren, abrir datepicker y re-seleccionar.
3. Scroll hasta el panel sticky de reserva; esperar que renderice precio por noche y total.
4. Capturar:
  - `precio_vigente_total` (texto no tachado `$505 en total`)
  - `precio_por_noche` (`$253 por noche`)
  - `precio_original_tachado` (si `<del>$562</del>` existe)
  - `descuento_text` (badge ej. `$56 de dto.`)
5. Derivar `monto_descuento` y `porcentaje_descuento`:
  - Si `precio_original_tachado` y `precio_vigente_total` conocidos: `monto_descuento = original - vigente`; `porcentaje = monto_descuento / original * 100`.
6. Si DOM incompleto → intentar XHR rates.

## Mapeo de campos y reglas
- Precio por noche: DOM directo si disponible; caso alterno JSON/XHR (`nightly`, `perNight`). Si sólo total: dividir por nights.
- Precio total vigente: del DOM (`… en total`). Si XHR `totalPrice` existe validar consistencia.
- Precio original tachado: `<del>` contenido monetario; si existe, considerar como base para descuento.
- Desayuno: buscar `desayuno`, `breakfast`, `includes breakfast`. Ausencia → `No`.
- WiFi: buscar `wifi`, `wi-fi`, `internet`. Ausencia → `No`.
- Moneda: derivar de símbolo (`$`, `€`) y/o código en JSON, normalizar.

## Validaciones
- Validar rango (10 <= precio_por_noche <= 10000).
- Moneda reconocida.
- Si descuento presente: `precio_original_tachado > precio_vigente_total`.
- Consistencia DOM vs XHR.

## Errores y métricas
Errores: `EXPEDIA_PRICE_NOT_FOUND`, `EXPEDIA_DISCOUNT_AMBIGUOUS`, `EXPEDIA_AMENITIES_NOT_FOUND`, `EXPEDIA_DATE_NOT_APPLIED`.
Métricas: tasa de éxito DOM, fallback depth, porcentaje de listings con descuento, resolución amenities.

## Estructura de salida (contrato)
```
ExpediaQuote {
  precio_total_vigente: float,
  precio_por_noche: float,
  currency: str,
  incluye_desayuno: 'Sí'|'No',
  wifi_incluido: 'Sí'|'No',
  precio_original_tachado: float | null,
  monto_descuento: float | null,
  porcentaje_descuento: float | null,
  nights: int,
  check_in: date,
  fuente: 'dom'|'api'|'json'|'regex',
  quality: float,
  evidencias?: {
    selector_total?: str,
    selector_por_noche?: str,
    selector_tachado?: str,
    badge_descuento?: str
  },
  errores?: [codigo]
}
```

## Recomendaciones de implementación
- Priorizar DOM; XHR para validación y fallback.
- Tests: fixture con descuento (tachado + badge) y fixture sin descuento.
- Verificar cálculo de porcentaje (tolerancia ±0.5%).
- Registrar evidencia textual para auditoría de cambios en layout.

---
Fin de metodología Expedia definitiva
