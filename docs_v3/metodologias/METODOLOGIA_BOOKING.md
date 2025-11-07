# Metodología de Extracción – Booking (V3 Definitiva)

Fecha: 2025-11-07 (actualizada con relevamiento manual)

## Objetivo
Extraer de forma reproducible:
- Precio total del período y precio por noche (valor base normalizable)
- Incluye desayuno (Sí/No) y evidencia textual (p.ej. "Desayuno americano incluido")
- WiFi incluido (Sí/No) (preferir indicador "WiFi gratis")
- Fecha de referencia (check-in)

## Consideraciones específicas
Booking presenta un breakdown dependiente de seleccionar explícitamente una habitación/cantidad (el usuario debió cambiar el selector de cantidad de 0 a 1 para habilitar el resumen). Los parámetros de fecha en la URL funcionan si se valida visualmente (etiquetas de llegada/salida). Limpieza se descarta como dato en V3.

## Estrategia Multicapa
1. DOM (resumen de reserva tras seleccionar cantidad de habitaciones) – fuente principal de precio total vigente, moneda y impuestos.
2. API/XHR (si aparece un endpoint de pricing/availability) – validación cruzada.
3. JSON embebido / JS variables – respaldo.
4. Regex – último recurso.

## Flujo operativo
1. Navegar a URL con parámetros `checkin`, `checkout`, `group_adults`, `group_children`, `no_rooms`, `selected_currency`.
2. Verificar visualmente fechas (botones con texto `vie, 7 nov` etc.). Si no coinciden, abrir calendario y seleccionar manualmente.
3. Seleccionar cantidad de habitaciones (cambiar de 0 a 1 en el `<select>` correspondiente) para que aparezca el resumen y precio total.
4. Capturar precio total (incluye descuentos aplicados). Identificar si hay impuestos/cargos adicionales (`+ US$147 de impuestos y cargos`) y sumar a total final si no está incluido.
5. Derivar precio por noche: `total_final / nights`.

## Mapeo de campos y reglas
- Precio total: leer del resumen (ej. `US$323`). Si hay línea de impuestos/cargos separado y el total mostrado NO los incluye, sumar.
- Precio por noche: total_final / nights (redondeo 2 decimales).
- Desayuno: buscar en amenities y en condiciones de la habitación (`Desayuno`, `Breakfast included`, `Desayuno americano incluido`). Si presente y no tachado → Sí, caso contrario → No.
- WiFi: `WiFi gratis` → Sí; ausencia o texto tachado/no disponible → No.
- Moneda: parsear prefijo (`US$`, `€`, etc.) y normalizar a ISO.

## Interacción y tasas variantes
- Booking muestra a veces la selección de tarifa (non-refundable, breakfast included). Debemos registrar la `rate_plan` usada para la observación.

## Validaciones
- Rango de precio y moneda (10 <= precio_por_noche <= 10000).
- Consistencia entre DOM y XHR.
- Confirmar que nights se corresponde con diferencia de fechas (check-out - check-in).

## Errores y métricas
Código de errores: `BOOKING_PRICE_NOT_FOUND`, `BOOKING_TAX_AMBIGUOUS`, `BOOKING_AMENITIES_NOT_LOADED`, `BOOKING_ROOM_SELECTION_REQUIRED`.
Métricas: tasa de éxito, fallback depth, porcentaje de observaciones con impuestos integrados, disponibilidad de desayuno.

## Estructura de salida (contrato)
```
BookingQuote {
  precio_total: float,
  precio_por_noche: float,
  currency: str,
  incluye_desayuno: 'Sí'|'No',
  wifi_incluido: 'Sí'|'No',
  impuestos_cargos_extra: float | null,   // si se desglosan separados
  nights: int,
  check_in: date,
  fuente: 'dom'|'api'|'json'|'regex',
  quality: float, // score heurístico (fuente + validaciones)
  evidencias?: {
    selector_total?: str,
    selector_impuestos?: str,
    desayuno_text?: str,
    wifi_text?: str
  },
  errores?: [codigo]
}
```

## Recomendaciones de implementación
- Priorizar DOM tras selección de habitación; XHR sólo para validación cruzada.
- Tests: fixture con caso impuestos incluidos y caso impuestos separados.
- Manejar descuentos: si existe precio tachado y precio vigente, usar vigente.
- Fallback si no se puede seleccionar habitación: registrar `BOOKING_ROOM_SELECTION_REQUIRED`.

---
Fin de metodología Booking definitiva
