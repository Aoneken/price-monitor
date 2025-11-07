# SCRAPING & INGESTA V3

## 1. Objetivo
Reemplazar arquitectura sincrónica por pipeline resiliente, observable y extensible multi-fuente.

## 2. Capas
| Capa | Función |
|------|---------|
| Tarea | Define lote de monitoreo (establecimiento, rango fechas) |
| Dispatcher | Divide tareas en sub-tareas Listing+Fecha |
| Robot Worker | Ejecuta extracción para (Listing, Fecha) |
| Normalizer | Convierte precio bruto a normalizado (moneda base) |
| Persistor | Escribe observaciones y emite eventos |

## 3. Tipos de Fuente
- `scrape`: Robots con Playwright.  
- `api`: Adaptadores (ej: API de PMS).  
- `manual`: Cargas CSV.  

## 4. Interfaz de Robot (SDK)
```python
class AbstractRobotV3(Protocol):
    name: str
    version: str
    def prepare(self, listing: ListingContext) -> None: ...
    def fetch(self, listing: ListingContext, fecha_noche: date) -> RawResult: ...
    def detect_block(self, page) -> bool: ...
    def close(self) -> None: ...
```
`RawResult`:
```python
@dataclass
class RawResult:
    precio_total: float
    noches_consultadas: int
    moneda: str
    impuestos_flag: bool
    desayuno_flag: bool
    html_fragment: str
    error_code: Optional[str]
    blocked: bool
```

## 5. Estrategia Multi-Extracción
Prioridad por técnicas:  
1. Network API Interception.  
2. Embedded window data.  
3. Selectores DOM jerarquizados.  
4. Heurística regex inteligente.  

## 6. Manejo de Bloqueos
- Registrar evento `RobotBlocked` con: plataforma, listing_id, selector_version, attempt.  
- Incrementar contador en memoria / Redis.  
- Si > threshold: pausar nuevas tareas plataforma 10 min (circuit breaker).  

## 7. Rate Limiting Adaptativo
Algoritmo:
- Inicial min_delay, max_delay.  
- Si bloqueos suben → aumentar delay dinámicamente + reducir concurrencia.  
- Si éxito sostenido → permitir reducción.  

## 8. Retries Inteligentes
- Retries base = 2.  
- Si error transitorio (timeout) → exponential backoff.  
- Si error selector → probar fallback next selector set.  

## 9. Actualización de Selectores
- Archivo JSON versionado.  
- Validación automática (lint selectores + prueba smoke).  
- Publicación genera evento `SelectorsUpdated`.  
- Robots cargan en `prepare()` según versión activa.  

## 10. Validación de Precio (post-fetch)
```python
def validate(raw: RawResult) -> ValidationOutcome:
    checks = [range_check, variation_check, currency_check]
    score = aggregate(checks)
    return ValidationOutcome(valid=score>0.6, quality=score)
```

## 11. Pipeline de Transformación
```
RawResult -> validate -> create PriceObservation -> normalize (FX) -> emit PriceNormalizedCreated
```

## 12. Concurrencia
Uso `asyncio` + semáforo por plataforma (limita navegadores simultáneos).  
Pooling de navegadores por robot para reuso contextos.  

## 13. HTML Snapshot
Fragmento de precio recortado (no página completa) para disminuir almacenamiento y permitir verificación manual.

## 14. Métricas Clave
| Métrica | Descripción |
|---------|-------------|
| scrape_duration_seconds | Latencia extracción por listing |
| scrape_block_events_total | Bloqueos detectados |
| scrape_retries_total | Reintentos realizados |
| price_validation_failure_total | Fallos de validación |

## 15. Fallback API
Si plataforma provee API oficial / semioficial, adaptador puede sustituir robot (configurable) y marcar fuente_tipo=api.

## 16. Seguridad Anti-Detección
- Rotación User-Agent / fingerprint parcial.  
- Randomización viewport mínima.  
- Proxy pool (futuro).  
- Evitar patrones: orden aleatorio de selectores, esperas jitter.  

## 17. Logging Estructurado (Ejemplo)
```json
{
  "ts":"2025-11-07T10:05:22Z",
  "level":"INFO",
  "event":"PriceExtractedRaw",
  "listing_id":42,
  "platform":"Airbnb",
  "duration_ms":1834,
  "blocked":false,
  "robot_version":"airbnb-v2.3.1"
}
```

## 18. Roadmap Scraping
| Fase | Entrega |
|------|---------|
| S1 | SDK Robots + Adapter API base |
| S2 | Event Bus + métricas Prometheus |
| S3 | Circuit breaker + rate adaptativo |
| S4 | Proxy rotation + ML anomaly detector |

---
Fin del documento de scraping e ingesta V3.
