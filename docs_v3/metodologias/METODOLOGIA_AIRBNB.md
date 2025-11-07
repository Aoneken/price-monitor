# Metodología de Extracción – Airbnb (V3)

Fecha: 2025-11-07 (actualizado con validación manual del usuario)
Estado: Metodología definitiva (lista para implementación)

## Objetivo
Diseñar una metodología robusta y reproducible para extraer:
1. Precio total del período y precio por noche (valor base normalizable)
2. Incluye desayuno (Sí/No)
3. WiFi incluido (Sí/No)
4. Fecha de referencia de cada observación

## Consideraciones Generales
Airbnb es una SPA (React/Next) con contenido dinámico, múltiples fuentes internas de datos (JSON embebido, Apollo/Apollo-like state) y mecanismos anti-bot. Las fechas en URL pueden no aplicarse directamente; sin embargo, en la evidencia provista por el usuario los parámetros en la URL funcionaron siempre que se verifique visualmente en el UI (check-in/out visibles). Limpieza deja de ser un dato de interés (se descarta cualquier lógica/medición de cleaning fee).

## Estrategia Multicapa
Orden de prioridad de fuentes (fallback):
1. DOM con breakdown visible (preferido): abrir “Mostrar el desglose del precio” y leer el total por N noches y la moneda.
2. API interceptada (requests XHR): si se identifica endpoint de pricing/availability, validar contra el DOM abierto.
3. JSON embebido en `<script>` (ej. `data-state`/`__PRELOADED_STATE__`) como respaldo.
4. Heurística minimal (regex) sobre HTML como último recurso.

Cada capa produce un objeto `RawQuote` con: `{precio_total, noches, currency, fees_detalle, services, html_snapshot_path, source_layer}`.

## Flujo de Interacción
1. Construir URL con `check_in`, `check_out`, `adults=…`, `guests=…` y `currency=USD` (o moneda deseada). Navegar.
2. Verificar visualmente (DOM) que las fechas están aplicadas: leer `data-testid="change-dates-checkIn"` y `…checkOut` y comparar con los valores esperados.
3. Si las fechas no están correctas o no hay precio, abrir el datepicker y seleccionar fechas manualmente.
4. Abrir el panel “Mostrar el desglose del precio” (siempre que esté disponible) para extraer el total exacto y la moneda. El UI suele mostrar dos importes cuando hay descuento: uno tachado (precio original) y uno vigente. Tomar el vigente (no tachado).
5. Registrar número de noches “por N noches” desde el texto adyacente para confirmar `nights`.

## Extracción de precio total y por noche
- En el breakdown visible, capturar el importe “total” mostrado para el período (ej. `$665,03 USD` para 2 noches). Este es el valor vigente (si hay dos importes, descartar el tachado/original).
- Parsear moneda y número con soporte de localización: separar miles y decimales (coma o punto según UI). Normalizar a float y moneda ISO (USD/EUR/ARS, etc.).
- Derivar `precio_por_noche = total / nights`. Redondear a 2 decimales, mantener precisión interna en float.
- Si el breakdown no está disponible, utilizar API/XHR o JSON embebido para calcular total y nights, y replicar la validación anterior.
- Validar rango razonable (10 <= precio_por_noche <= 10000).

## Desayuno Incluido (Sí/No)
Fuente: sección de amenities (“Qué ofrece este lugar”).
1. Buscar `desayuno`/`breakfast` en español/inglés. 
2. Si aparece y no está tachado (no envuelto en `<del>` ni marcado como no disponible) → `Sí`; en caso contrario → `No`.
3. Guardar snippet de evidencia para auditoría.

## WiFi Incluido (Sí/No)
1. Buscar amenities `wifi/wi-fi/internet`. 
2. Si el texto aparece tachado dentro de `<del>` → `No`. Si aparece disponible → `Sí`.
3. (Opcional) Diferenciar gratuito vs de pago si el texto lo indica.

## Limpieza
Se descarta cualquier extracción/registro de limpieza. No es un dato de interés en V3 y no debe formar parte del contrato de salida.

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

## Estructura de Datos Propuesta (AirbnbQuote)
```json
{
   "listing_id": "1413234233737891700",
   "check_in": "2026-01-06",
   "check_out": "2026-01-08",
   "nights": 2,
   "currency": "USD",
   "precio_total": 665.03,
   "precio_por_noche": 332.52,
   "incluye_desayuno": "Sí",
   "wifi_incluido": "Sí",
   "fuente": "dom_breakdown",
   "evidencias": {
      "selector_total": "span[aria-hidden=false] en panel de desglose",
      "selector_nights": "span:has-text('por N noches')",
      "amenities_snippets": ["Wifi", "Desayuno"]
   },
   "html_snapshot_path": "snapshots/airbnb/1413234233737891700_2026-01-06.html",
   "timestamp_scrape": "2025-11-07T14:25:11Z"
}
```

## Validaciones
- Rango precio base por noche.
- Moneda soportada (map configurable).
- Amenities: fuzzy matching (normalizar a minúsculas, quitar acentos).

## Errores Clasificados
| Código | Descripción | Acción |
|--------|-------------|--------|
| URL_NO_FECHAS | Fechas no aplicadas tras interacción | Reintentar selección calendar |
| PRICE_NOT_FOUND | No aparece breakdown de precio | Activar siguiente estrategia |
| AMENITIES_NOT_LOADED | Amenities vacíos | Scroll + reintentar parse |
| PRICE_DISCOUNT_AMBIGUOUS | Se detectan dos precios (tachado vs vigente) | Priorizar precio vigente observado en breakdown |

## Logging y Métricas
Métricas a capturar:
- `airbnb_price_extraction_success_rate`
- `airbnb_amenities_resolution_rate`
- `airbnb_strategy_fallback_depth`

Logs estructurados JSON por intento con estrategia y resultado.

## Próximos Pasos
1. Identificar endpoints reales de pricing (inspección manual Network). 
2. Definir selectores/paths concretos y versión base (v3.0-ALPHA). 
3. Implementar prototipo `AirbnbRobotV3` con pipeline de estrategias (DOM breakdown → XHR → JSON). 
4. Añadir tests con fixtures HTML del breakdown (precio total + “por N noches”) y de amenities con casos tachados `<del>`.

## Riesgos
- Cambio repentino en layout o API (mitigar con multi-fuente). 
- Bloqueo IP por frecuencia (mitigar con delays adaptativos). 
- Amenity breakfast puede faltar → preferir resultado `No` salvo evidencia explícita `Sí`.

---
Fin de la metodología definitiva Airbnb.
