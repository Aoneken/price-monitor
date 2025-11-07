# Fase 2 – Ingesta y Scraping

## Objetivo
Construir un SDK de robots con estrategias de extracción múltiples y contrato uniforme.

## Alcance
- AbstractRobotV3: interfaz única.
- ExtractionEngine: DOM + JSON embebido + API intercept + regex.
- Navigator: interacción (selección de fechas) cuando URL no aplica.
- SelectorRegistry: versionado y fallback de selectores.

## Criterios de aceptación
- Robot de Airbnb con interacción/fallback operativa.
- Eventos de scraping: intentos, fallos con códigos, éxitos.
- Métrica de tasa de éxito por plataforma.

## Lecciones heredadas relevantes
- Airbnb ignorando parámetros de fecha → Interacción o API.
- Selectores frágiles → Estrategias alternativas y health-check de selectores.
- Diferenciar "no disponible" de "error extracción".

## Metodología específica: Airbnb (definición)

Objetivo: extraer Precio total del período y Precio por noche, Desayuno (Sí/No), WiFi (Sí/No), con fecha de referencia. (Limpieza se descarta como dato no relevante en V3.)

1) Fechas y verificación
- Intentar primero con parámetros en URL (`check_in`, `check_out`, `adults`, `currency`).
- Verificar en UI: `data-testid="change-dates-checkIn"` y `…checkOut` deben coincidir. Si no, abrir calendario y seleccionar manualmente.

2) Orden de estrategias (fallback)
- DOM (panel de desglose) → capturar total por N noches y moneda; y lista de amenities.
- API/XHR: validar/preferir si disponible y consistente con el DOM.
- JSON embebido: respaldo.
- Regex: último recurso.

3) Mapeo de campos
- Precio total: del breakdown vigente (no tomar el precio tachado/original si existe descuento).
- Precio por noche: `total / nights`.
- Desayuno: amenity `desayuno/breakfast` disponible y no tachado → Sí, si no → No.
- WiFi: amenity `wifi/wi-fi/internet` no tachado → Sí; tachado `<del>` → No.
- Moneda: del breakdown/DOM, normalizar ISO.

4) Errores y métricas
- Códigos: `URL_NO_FECHAS`, `PRICE_NOT_FOUND`, `AMENITIES_NOT_LOADED`, `PRICE_DISCOUNT_AMBIGUOUS`.
- Métricas: tasa de éxito, profundidad de fallback, resolución de amenities.

5) Anti-bot mínimo
- Rotación de UA, pequeñas interacciones (scroll/hover), esperas cortas aleatorias; modo no headless para validación.

6) Contrato de salida (resumen)
```
AirbnbQuote {
	precio_total: float,
	precio_por_noche: float,
	currency: str,
	incluye_desayuno: 'Sí'|'No',
	wifi_incluido: 'Sí'|'No',
	nights: int,
	check_in: date,
	fuente: 'api'|'json'|'dom'|'regex',
	quality: float,
	errores?: [codigo]
}
```

Nota: ver detalles ampliados y casos límite en `docs_v3/metodologias/METODOLOGIA_AIRBNB.md`.

---

## Metodología específica: Booking (definición)

Objetivo: extraer Precio total, Precio por noche, Desayuno (Sí/No), WiFi (Sí/No), con fecha de referencia. Impuestos y cargos se suman al total final.

1) Interacción y selección de habitación
- Navegar con parámetros `checkin`, `checkout`, `group_adults`, `selected_currency`.
- Verificar fechas en UI (botones visibles).
- **Seleccionar cantidad de habitaciones** (cambiar de 0 a 1 en `<select>`) para habilitar resumen.

2) Orden de estrategias (fallback)
- DOM (resumen de reserva) → precio total + impuestos separados (sumar).
- API/XHR: validación cruzada.
- JSON embebido: respaldo.
- Regex: último recurso.

3) Mapeo de campos
- Precio total: capturar del resumen; si hay línea "+ US$X de impuestos y cargos" → sumar.
- Precio por noche: total_final / nights.
- Desayuno: buscar en amenities y condiciones de habitación (`Desayuno americano incluido`). Presente → Sí; ausente → No.
- WiFi: buscar `WiFi gratis` → Sí; ausente/tachado → No.
- Moneda: del prefijo/DOM, normalizar ISO.

4) Errores y métricas
- Códigos: `BOOKING_PRICE_NOT_FOUND`, `BOOKING_TAX_AMBIGUOUS`, `BOOKING_ROOM_SELECTION_REQUIRED`.
- Métricas: tasa éxito, fallback depth, % observaciones con impuestos integrados.

5) Validaciones
- Rango precio (10–10000 por noche).
- Consistencia entre total mostrado y suma de componentes.

6) Contrato de salida (resumen)
```
BookingQuote {
	precio_total: float,
	precio_por_noche: float,
	currency: str,
	incluye_desayuno: 'Sí'|'No',
	wifi_incluido: 'Sí'|'No',
	impuestos_cargos_extra: float | null,
	nights: int,
	check_in: date,
	fuente: 'dom'|'api'|'json'|'regex',
	quality: float,
	errores?: [codigo]
}
```

Nota: ver detalles completos en `docs_v3/metodologias/METODOLOGIA_BOOKING.md`.

---

## Metodología específica: Expedia (definición)

Objetivo: extraer Precio total vigente (post-descuento), Precio por noche, Precio original tachado (si hay descuento), Monto y porcentaje de descuento, WiFi, Desayuno.

1) Interacción y verificación
- Navegar con `chkin/chkout` (o `checkIn/checkOut`), adults, currency.
- Verificar fechas en datepickers (`data-testid="uitk-date-selector-input*"`).
- Scroll hasta panel sticky de reserva; esperar renderizado completo.

2) Orden de estrategias (fallback)
- DOM sticky card (precio por noche, total, precio tachado, badge descuento).
- API/XHR rates: validación cruzada.
- JSON embebido: respaldo.
- Regex: último recurso.

3) Mapeo de campos
- Precio total vigente: texto no tachado `$505 en total`.
- Precio por noche: `$253 por noche`.
- Precio original tachado: `<del>$562</del>` (si existe).
- Descuento: extraer badge `$56 de dto.`; calcular: `monto_descuento = original - vigente`, `porcentaje = (monto/original)*100`.
- Desayuno: buscar amenities/textos. Ausente → No.
- WiFi: buscar amenities. Ausente → No.
- Moneda: símbolo y normalizar ISO.

4) Errores y métricas
- Códigos: `EXPEDIA_PRICE_NOT_FOUND`, `EXPEDIA_DISCOUNT_AMBIGUOUS`, `EXPEDIA_DATE_NOT_APPLIED`.
- Métricas: tasa éxito DOM, fallback depth, % listings con descuento.

5) Validaciones
- Rango (10–10000 por noche).
- Si descuento: `precio_original_tachado > precio_vigente`.
- Porcentaje descuento válido (0–100%).

6) Contrato de salida (resumen)
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
	errores?: [codigo]
}
```

Nota: ver detalles completos en `docs_v3/metodologias/METODOLOGIA_EXPEDIA.md`.
