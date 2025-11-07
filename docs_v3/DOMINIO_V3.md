# DOMINIO V3 – Modelo Conceptual

## 1. Contexto
El dominio representa el universo de observación de precios y disponibilidad de alojamientos en múltiples plataformas. Se requiere enriquecer el modelo para soportar fuentes diversas y metadatos de calidad.

## 2. Entidades Principales
| Entidad | Descripción | Notas |
|---------|-------------|-------|
| Establecimiento | Unidad lógica monitoreada | Se conserva (ID estable) |
| FuentePlataforma | Representa origen (Booking, Airbnb, API_X) | Tiene metadata de health |
| Listing | Instancia específica (URL o ID externo) | Anterior `Plataformas_URL` refinada |
| PriceObservation | Registro de precio bruto (por ejecución) | Noches, total, moneda, impuestos brutos |
| PriceNormalized | Precio por noche normalizado a moneda base | Resultante de transformación |
| AvailabilityObservation | Señal de disponibilidad / ocupación inferida | Separado de precio |
| SelectorVersion | Versión de configuración DOM usada | Facilita depuración |
| RobotExecution | Evento de ejecución con métricas | Duración, reintentos, outcomes |
| EventLog | Registro de evento de dominio | Para reconstrucción e investigaciones |

## 3. Relaciones (Texto)
```
Establecimiento 1--* Listing
Listing 1--* PriceObservation
PriceObservation 1--1 PriceNormalized
Listing 1--* AvailabilityObservation
RobotExecution *--* PriceObservation (por referencia)
SelectorVersion 1--* RobotExecution
```

## 4. Atributos Clave
| Entidad | Atributos Clave |
|---------|-----------------|
| Establecimiento | id, nombre, zona, tags opcionales |
| Listing | id, establecimiento_id, plataforma, external_ref, url, activa, created_at |
| PriceObservation | id, listing_id, fecha_noche, fecha_ingesta, noches_consultadas, precio_total_original, moneda_original, impuestos_flag, desayuno_flag, fuente_tipo (scrape/api/manual), raw_hash, robot_version, calidad_score |
| PriceNormalized | id, price_observation_id, precio_por_noche, moneda_base, fx_rate, fx_source, normalization_timestamp |
| AvailabilityObservation | id, listing_id, fecha_noche, fecha_ingesta, estado (disponible/ocupado/unknown), metodo_inferencia |
| SelectorVersion | id, plataforma, version_semver, checksum_json, published_at |
| RobotExecution | id, listing_id, inicio, fin, duracion_ms, reintentos, resultado_estado, error_code, bloqueo_detectado, selector_version_id |
| EventLog | id, event_type, payload_json, created_at |

## 5. Reglas de Negocio
1. Un `PriceObservation` nunca se borra físicamente (auditoría).  
2. Un `PriceNormalized` puede recalcularse si cambian reglas FX → se crea nueva fila, no se sobreescribe.  
3. Inferencia ocupación: Si para fecha_noche se prueban 3,2,1 noches y todas fallan → AvailabilityObservation.estado=ocupado (método=fallback_depth).  
4. Calidad: precio fuera de rango dinámico (percentil global ± threshold) marca calidad_score bajo.  
5. Un Listing inactivo no genera tareas nuevas pero conserva histórico.  
6. SelectorVersion usada se asocia a cada RobotExecution; si error_code indica fallback, se registra.  

## 6. Eventos de Dominio
| Evento | Descripción | Emisor |
|--------|-------------|--------|
| PriceQueryRequested | Solicitud de monitoreo | UI/API |
| RobotStarted | Inicio extracción listing | Worker |
| RobotBlocked | Detección anti-bot | Robot |
| PriceExtractedRaw | Precio bruto capturado | Robot |
| AvailabilityInferred | Señal disponibilidad calculada | Servicio Dominio |
| PriceNormalizedCreated | Generado precio normalizado | Normalizer |
| PriceStored | Persistencia confirmada | Persistencia |
| SelectorsUpdated | Publicada nueva versión selectores | Admin Tool |
| RobotExecutionCompleted | Fin proceso individual | Worker |

## 7. Ciclo de Vida de un Precio
1. Solicitud crea eventos `PriceQueryRequested`.  
2. Robot ejecuta → `PriceExtractedRaw`.  
3. Servicio normalización → calcula fx → `PriceNormalizedCreated`.  
4. Persistencia → `PriceStored`.  
5. Dashboard consume vistas materializadas.  

## 8. Validaciones
| Regla | Tipo |
|-------|------|
| precio_total_original >= 0 | CHECK |
| moneda_original IN lista soportada | CHECK |
| noches_consultadas IN (1,2,3) | CHECK |
| fx_rate > 0 | CHECK |
| calidad_score BETWEEN 0 AND 1 | CHECK |

## 9. Estrategia de Normalización de Moneda
- Tabla `fx_rates` (fecha, moneda, rate_vs_base, source).  
- Uso último rate disponible <= fecha_ingesta; si falta se marca estado `pending_fx`.  

## 10. Criterios para Calidad Score (0..1)
- Base: rango razonable (percentil 5 a 95).  
- Penalización si precio sin impuestos declarado pero selector indica presencia.  
- Penalización si variance respecto precio anterior > X%.  

## 11. Casos Especiales
- Feriados / Eventos: Tabla `calendar_events` enlazable para futuras recomendaciones.  
- Moneda dinámica: si plataforma reporta múltiples monedas, se crea observación por moneda.  

## 12. Persistencia de Linaje
`raw_hash = SHA256(html_fragment || selector_version || platform || listing_id || fecha_noche)` para rastreabilidad.  

## 13. Ejemplos de Payload Evento (JSON)
```json
{
  "event_type": "PriceExtractedRaw",
  "listing_id": 42,
  "fecha_noche": "2025-12-24",
  "precio_total_original": 480.00,
  "moneda_original": "USD",
  "noches_consultadas": 3,
  "robot_version": "airbnb-v2.3.1",
  "selector_version": "airbnb-selectors-2025.11.07",
  "raw_hash": "a8fd..."
}
```

## 14. Evolución Futura
- Agregar entidad `CompetitorGroup` para análisis comparativo.  
- Añadir `Recommendation` basada en modelo predictivo (referencia PriceNormalized y eventos).  

---
Fin del documento de dominio V3.
