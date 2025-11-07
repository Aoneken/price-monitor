# Tests V3 - Suite de Validación de Metodologías

## Resumen
Tests unitarios y de contrato para validar las metodologías definitivas de extracción de datos de:
- **Airbnb**: parsing de precio total/por noche, amenities (WiFi/Desayuno tachados), validaciones de rango.
- **Booking**: parsing de precio + impuestos separados, selección de habitación, amenities.
- **Expedia**: parsing de descuentos (precio tachado, vigente, badge), cálculo de porcentajes, validaciones.

## Estructura
```
tests_v3/
├── __init__.py
├── test_parsers_airbnb.py      # 9 tests (precio, noches, amenities, contrato)
├── test_parsers_booking.py     # 8 tests (precio+impuestos, amenities, contrato)
├── test_parsers_expedia.py     # 9 tests (descuento, precio tachado, contrato)
└── fixtures/                   # (reservado para HTML fixtures)
```

## Ejecutar tests
```bash
source .venv/bin/activate
pytest tests_v3/ -v
```

## Resultados
✅ **26/26 tests pasados** (0.05s)

### Cobertura por plataforma
- Airbnb: 9/9 ✅
  - Parsing precio simple y con miles
  - Cálculo precio por noche con tolerancia redondeo
  - Detección amenities con elementos tachados
  - Validación contrato AirbnbQuote
- Booking: 8/8 ✅
  - Parsing precio base + impuestos separados
  - Cálculo total final
  - Amenities (WiFi gratis, desayuno incluido)
  - Validación contrato BookingQuote (con y sin impuestos)
- Expedia: 9/9 ✅
  - Parsing precio vigente, tachado, badge descuento
  - Cálculo porcentaje descuento
  - Validación contrato ExpediaQuote (con y sin descuento)

## Casos límite validados
- Precio con separador de miles: `$1.200,00` → 1200.0 ✅
- Amenities tachados: `<del>Wifi</del>` → No ✅
- Impuestos separados: `+ US$147` → suma correcta ✅
- Descuento: original 562, vigente 505 → 10.14% ✅
- Validación rango: 10 <= precio_por_noche <= 10000 ✅
- División con tolerancia redondeo: ±0.01 ✅

## Próximos pasos
1. Añadir fixtures HTML reales capturados de exploraciones.
2. Implementar robots V3 usando estos parsers como base.
3. Tests de integración con Playwright (navegación + extracción end-to-end).
4. Monitoreo de cambios en layout (snapshot testing).
