# CONTRATOS & INTERFACES V3

## 1. Objetivo
Estandarizar interfaces internas para garantizar intercambiabilidad y minimizar acoplamiento.

## 2. Contrato Robot
```python
@dataclass
class ListingContext:
    listing_id: int
    plataforma: str
    url: str
    external_ref: str | None
    metadata: dict

@dataclass
class ExtractionOutcome:
    success: bool
    raw_result: RawResult | None
    error_code: str | None
    blocked: bool
    attempts: int
    duration_ms: int

class AbstractRobotV3(ABC):
    name: str
    version: str
    def prepare(self, context: ListingContext) -> None: ...
    def fetch(self, context: ListingContext, fecha_noche: date) -> RawResult: ...
    def shutdown(self) -> None: ...
```

## 3. Contrato Event Publisher
```python
class EventPublisher(Protocol):
    def publish(self, event_type: str, payload: dict) -> None: ...
```

## 4. Contrato Repository
```python
class PriceObservationRepository(Protocol):
    def save_raw(self, po: PriceObservation) -> PriceObservation: ...
    def fetch_range(self, listing_id: int, start: date, end: date) -> list[PriceObservation]: ...
```

## 5. DTOs Expuestos (API REST Futuro)
```json
GET /api/v1/listings/42/prices?from=2025-11-01&to=2025-11-10
{
  "listing_id":42,
  "currency":"USD",
  "prices":[{"date":"2025-11-01","avg":125.50,"samples":3}]
}
```

## 6. Contrato Normalizador
```python
class Normalizer(Protocol):
    def normalize(self, raw: RawResult, fx_provider: FXProvider) -> NormalizedPrice: ...
```

## 7. Contrato FX Provider
```python
class FXProvider(Protocol):
    def get_rate(self, moneda: str, fecha: date) -> float | None: ...
```

## 8. Contrato Validation Engine
```python
class ValidationEngine(Protocol):
    def score(self, raw: RawResult, history: list[float]) -> float: ...
```

## 9. Códigos de Error Estandarizados
| Código | Significado | Acción |
|--------|-------------|--------|
| BLOCKED_CAPTCHA | CAPTCHA detectado | Aumentar delay / rotar proxy |
| SELECTOR_NOT_FOUND | Selectores fallan | Registrar y probar fallback |
| NETWORK_TIMEOUT | Timeout navegación | Retry con backoff |
| PRICE_OUTLIER | Precio fuera rango | Marcar calidad baja |
| FX_RATE_MISSING | Falta tipo de cambio | Marcar pendiente normalización |

## 10. Versionamiento de Interfaces
- Cada interfaz tiene semver independiente (robot-sdk v1.0.0).  
- Cambios incompatibles → bump mayor y adaptadores legacy.  

## 11. Testing de Contratos
- Pruebas de contrato (pytest) con fixtures para robots simulados.  
- Validar que `fetch()` siempre retorna `RawResult` consistente.  

## 12. OpenAPI (Futuro)
Generación automática de spec `openapi.yaml` desde decoradores FastAPI.  

---
Fin del documento de contratos V3.
