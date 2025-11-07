# Metodología de Extracción – Airbnb (V3)

Fecha: 2025-11-07
Estado: Definición inicial (antes de implementación)

## Objetivo
Diseñar una metodología robusta y reproducible para extraer:
1. Precio por noche (valor base normalizable)
2. Incluye desayuno (Sí/No)
3. WiFi incluido (Sí/No)
4. Limpieza se paga aparte (Sí/No)
5. Fecha de referencia de cada observación

## Consideraciones Generales
Airbnb es una SPA (React/Next), con contenido dinámico, múltiples fuentes internas de datos (JSON embebido, Apollo state, scripts), y mecanismos anti-bot. Las fechas en URL pueden no aplicarse directamente sin interacción.

## Estrategia Multicapa
Orden de prioridad de fuentes (fallback):
1. API interceptada (requests XHR) – si se identifica endpoint de pricing/availability
2. JSON embebido en `<script>` (ej. `data-state` o `__PRELOADED_STATE__`)
3. Apollo Client cache / window.__INITIAL_DATA__
4. DOM estructurado (selectores CSS actuales)
5. Heurística regex sobre HTML completo (último recurso)

Cada capa produce un objeto `RawQuote` con: `{precio_total, noches, currency, fees_detalle, services, html_snapshot_path, source_layer}`.

## Flujo de Interacción
1. Cargar URL base del listing sin parámetros de fechas.
2. Abrir calendar picker y seleccionar check-in y check-out (interacción simulada):
   - Identificar nodos `data-testid='calendar-day-*'` o atributos accesibles.
   - Esperar confirmación visual de fechas aplicadas (elementos de fecha en resumen de reserva).
3. Esperar aparición de contenedor de precio / breakdown.
4. Recolectar fuente primaria (API / JSON) antes de consultar DOM.

## Extracción de Precio por Noche
- Si API retorna `priceItems` con `amount` y `type='BASE'`, calcular `precio_base_noche = total_base / noches`.
- Si sólo hay `totalPrice` y `nights`, `precio_base_noche = totalPrice / nights` (sin tarifas de limpieza/impuestos).
- Validar rango razonable (10 <= precio_base_noche <= 10000).
- Registrar currency (ej. USD, EUR, ARS).

## Desayuno Incluido (Sí/No)
Airbnb rara vez usa campo explícito para desayuno en JSON; puede estar en:
- Sección "What this place offers" (lista de amenities)
- Texto descriptivo del host

Metodología:
1. Parsear bloques de amenities (JSON / DOM list items) buscando keywords multi-idioma:
   - Español: `desayuno`, `incluye desayuno`
   - Inglés: `breakfast`, `free breakfast`
2. Si match → `incluye_desayuno = 'Sí'` else `'No'`.
3. Registrar `evidencia_desayuno` (texto encontrado) para auditoría.

## WiFi Incluido (Sí/No)
Más estable en amenities.
1. Buscar en amenities: `wifi`, `wi-fi`, `internet`.
2. Si aparece marcado como disponible → `'Sí'`, si no se encuentra → `'No'`.
3. Diferenciar `wifi gratuito` vs `wifi de pago` si texto contiene `fee`, `extra charge`.

## Limpieza Se Paga Aparte (Sí/No)
- Revisar breakdown de costos (DOM / JSON). Airbnb suele listar `Cleaning fee`.
1. En estructura de tarifas JSON o DOM, localizar ítems con `type='CLEANING'` o texto `cleaning fee` / `tarifa de limpieza`.
2. Si existe y `amount > 0` → `limpieza_aparte = 'Sí'`, caso contrario `'No'`.
3. Registrar monto limpieza separado para futura normalización.

## Fecha de Referencia
La fecha de la observación corresponde al check-in de la primera noche solicitada.
- Campo `fecha_noche_inicio = check_in`.
- Expandir a noches individuales si se requiere granularidad (Futuro: pipeline de expansión).
- Almacenar timestamp exacto de scraping para frescura.

## Anti-bot y Robustez
Medidas iniciales:
- Rotación de User-Agent.
- Pequeñas interacciones humanas simuladas (scroll, hover sobre calendario, pausa aleatoria 500–1500ms).
- Opcional: ejecución no headless para validación inicial.

## Estructura de Datos Propuesta (RawQuote)
```json
{
  "listing_id": "1413234233737891700",
  "check_in": "2025-12-15",
  "check_out": "2025-12-18",
  "nights": 3,
  "currency": "USD",
  "precio_total_base": 450.0,
  "precio_base_noche": 150.0,
  "cleaning_fee": 50.0,
  "incluye_desayuno": "No",
  "wifi_incluido": "Sí",
  "limpieza_aparte": "Sí",
  "services_detected": ["Wifi", "Kitchen", "Heating"],
  "fuente": "API_XHR",
  "html_snapshot_path": "snapshots/airbnb/1413234233737891700_2025-12-15.html",
  "extraction_strategies": ["api", "json_script", "dom"],
  "timestamp_scrape": "2025-11-07T14:25:11Z"
}
```

## Validaciones
- Rango precio base por noche.
- Moneda soportada (map configurable).
- Limpieza > 0 implica `limpieza_aparte='Sí'`.
- Amenities: fuzzy matching (normalizar a minúsculas, quitar acentos).

## Errores Clasificados
| Código | Descripción | Acción |
|--------|-------------|--------|
| URL_NO_FECHAS | Fechas no aplicadas tras interacción | Reintentar selección calendar |
| PRICE_NOT_FOUND | No aparece breakdown de precio | Activar siguiente estrategia |
| AMENITIES_NOT_LOADED | Amenities vacíos | Scroll + reintentar parse |
| CLEANING_FEE_AMBIGUOUS | Texto inconsistente | Log evidencia y marcar limpieza_aparte='No' provisional |

## Logging y Métricas
Métricas a capturar:
- `airbnb_price_extraction_success_rate`
- `airbnb_amenities_resolution_rate`
- `airbnb_cleaning_fee_detection_rate`
- `airbnb_strategy_fallback_depth`

Logs estructurados JSON por intento con estrategia y resultado.

## Próximos Pasos
1. Identificar endpoints reales de pricing (inspección manual Network). 
2. Definir selectores/paths concretos y versión base (v3.0-ALPHA). 
3. Implementar prototipo `AirbnbRobotV3` con pipeline de estrategias. 
4. Añadir test con fixture HTML + mock de JSON embebido.

## Riesgos
- Cambio repentino en layout o API (mitigar con multi-fuente). 
- Bloqueo IP por frecuencia (mitigar con delays adaptativos). 
- Amenity breakfast poco frecuente (puede devolver falsos negativos). 

---
Fin de la definición inicial Airbnb.
