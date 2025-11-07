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

Objetivo: extraer Precio por noche, Desayuno (Sí/No), WiFi (Sí/No), Limpieza aparte (Sí/No), con fecha de referencia.

1) Interacción necesaria de fechas
- No confiar en `checkin/checkout` en URL. Abrir calendario y seleccionar `check_in` y `check_out`.
- Verificar aplicación de fechas en el UI (resumen de reserva visible) antes de extraer.

2) Orden de estrategias (fallback)
- API/XHR: capturar respuesta de pricing/availability, preferida para breakdown y fees.
- JSON embebido: parsear `script` con estado inicial (Next/Apollo) para `priceItems`, `cleaning_fee`, `amenities`.
- DOM: leer breakdown visible y lista de amenities.
- Regex: último recurso sobre HTML para detectar montos/amenities.

3) Mapeo de campos
- Precio por noche: total_base / noches (o `nightly_price` si existe); validar 10–10000.
- Desayuno: buscar en amenities (ES/EN) términos `desayuno/breakfast`.
- WiFi: amenity `wifi/wi-fi/internet`.
- Limpieza aparte: ítem `cleaning fee` > 0 en breakdown.
- Moneda: del JSON/DOM, normalizar ISO.

4) Errores y métricas
- Códigos: `URL_NO_FECHAS`, `PRICE_NOT_FOUND`, `AMENITIES_NOT_LOADED`, `CLEANING_FEE_AMBIGUOUS`.
- Métricas: tasa de éxito, profundidad de fallback, detección de limpieza, resolución de amenities.

5) Anti-bot mínimo
- Rotación de UA, pequeñas interacciones (scroll/hover), esperas cortas aleatorias; modo no headless para validación.

6) Contrato de salida (resumen)
```
AirbnbQuote {
	precio_base_noche: float,
	currency: str,
	incluye_desayuno: 'Sí'|'No',
	wifi_incluido: 'Sí'|'No',
	limpieza_aparte: 'Sí'|'No',
	nights: int,
	check_in: date,
	fuente: 'api'|'json'|'dom'|'regex',
	quality: float,
	errores?: [codigo]
}
```

Nota: ver detalles ampliados en `docs_v3/METODOLOGIA_AIRBNB.md`.
