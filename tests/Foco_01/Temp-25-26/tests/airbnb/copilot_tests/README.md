# copilot_tests — Scripts de Pricing & Availability para Airbnb

Este directorio contiene scripts para extraer datos de disponibilidad y precios de listados de Airbnb.

## Scripts Disponibles

### 1. `get_prices_simple.py` (RECOMENDADO)

Script principal que genera un CSV con disponibilidad + precios por noche.

**Características:**

- ✅ Obtiene disponibilidad directamente de la API de Airbnb (PdpAvailabilityCalendar)
- ✅ Soporta múltiples modos de pricing:
  - Tasa fija por noche (`--fixed-rate`)
  - Archivo JSON con precios manuales (`--pricing-file`)
  - Solo disponibilidad (sin pricing)
- ✅ Incluye metadatos en el header del CSV (listing info, periodo, huéspedes)
- ✅ No requiere autenticación compleja

**Limitación:** El endpoint `stayCheckout` de Airbnb requiere autenticación con cookies/sesión completa, por lo que la obtención automática de precios exactos no es posible con llamadas simples a la API. Este script ofrece alternativas prácticas.

#### Uso Básico

```bash
# Solo disponibilidad (sin precios)
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-10 \
    --end 2025-12-20 \
    --guests 2 \
    --out tmp/availability.csv

# Con tasa fija por noche
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-10 \
    --end 2025-12-20 \
    --guests 2 \
    --fixed-rate 200 \
    --listing-name "Villa Carlos Paz Property" \
    --listing-url "https://www.airbnb.com.ar/rooms/928978094650118177" \
    --out tmp/prices_fixed.csv

# Con archivo de precios manuales
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-10 \
    --end 2025-12-20 \
    --guests 2 \
    --pricing-file tmp/manual_prices.json \
    --out tmp/prices_manual.csv
```

#### Parámetros

| Parámetro        | Requerido | Descripción                      | Ejemplo              |
| ---------------- | --------- | -------------------------------- | -------------------- |
| `--listing-id`   | ✅        | ID del listing de Airbnb         | `928978094650118177` |
| `--start`        | ✅        | Fecha inicio (YYYY-MM-DD)        | `2025-12-10`         |
| `--end`          | ✅        | Fecha fin (YYYY-MM-DD)           | `2025-12-20`         |
| `--guests`       | ❌        | Número de huéspedes (default: 2) | `4`                  |
| `--out`          | ✅        | Ruta del CSV de salida           | `tmp/output.csv`     |
| `--listing-name` | ❌        | Nombre del listing (para header) | `"Mi Cabaña"`        |
| `--listing-url`  | ❌        | URL del listing (para header)    | `https://...`        |
| `--fixed-rate`   | ❌        | Precio fijo por noche (USD)      | `200`                |
| `--pricing-file` | ❌        | Archivo JSON con precios         | `tmp/prices.json`    |
| `--currency`     | ❌        | Código de moneda (default: USD)  | `ARS`                |

**Nota:** `--fixed-rate` y `--pricing-file` son mutuamente exclusivos.

#### Formato del CSV de Salida

```csv
# Listing: Villa Carlos Paz Property
# Listing ID: 928978094650118177
# Listing URL: https://www.airbnb.com.ar/rooms/928978094650118177
# Period: 2025-12-10 to 2025-12-20
# Guests: 2
# Generated: 2025-11-08T10:30:00.123456
#
date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,notes
"2025-12-10","True","True","True","True","2","15","200.00","USD",""
"2025-12-11","True","True","True","True","2","15","200.00","USD",""
...
```

#### Formato del Archivo de Precios Manuales

Archivo JSON con formato `fecha: precio`:

```json
{
  "2025-12-10": 200.0,
  "2025-12-11": 200.0,
  "2025-12-12": 220.0,
  "2025-12-13": 220.0,
  "2025-12-14": 250.0
}
```

### 2. `get_prices.py` (EXPERIMENTAL - NO FUNCIONAL)

Script inicial que intentaba obtener precios directamente de `stayCheckout`. **No funciona** debido a las restricciones de autenticación de Airbnb.

**Problema:** El endpoint POST `/api/v3/stayCheckout` requiere:

- Cookies de sesión completas
- Tokens CSRF válidos
- Headers específicos del navegador
- Body complejo con `productId` codificado, `quickPayData`, etc.

**Estado:** Archivado para referencia. No se recomienda su uso.

## Workflow Recomendado

### Opción A: Tasa Fija (Para estimaciones rápidas)

Si conoces el precio promedio por noche:

```bash
python3 scripts/get_prices_simple.py \
    --listing-id <ID> \
    --start <FECHA_INICIO> \
    --end <FECHA_FIN> \
    --guests <NUM_HUESPEDES> \
    --fixed-rate <PRECIO_PROMEDIO> \
    --out output.csv
```

### Opción B: Precios Manuales (Para máxima precisión)

1. Visita manualmente el listing en Airbnb
2. Anota los precios por noche para el periodo deseado
3. Crea un archivo JSON con los precios:
   ```json
   {
     "2025-12-10": 195.5,
     "2025-12-11": 195.5,
     "2025-12-12": 220.0
   }
   ```
4. Ejecuta el script:
   ```bash
   python3 scripts/get_prices_simple.py \
       --listing-id <ID> \
       --start <FECHA_INICIO> \
       --end <FECHA_FIN> \
       --guests <NUM_HUESPEDES> \
       --pricing-file manual_prices.json \
       --out output.csv
   ```

### Opción C: Solo Disponibilidad

Para monitorear únicamente disponibilidad sin precios:

```bash
python3 scripts/get_prices_simple.py \
    --listing-id <ID> \
    --start <FECHA_INICIO> \
    --end <FECHA_FIN> \
    --guests <NUM_HUESPEDES> \
    --out availability.csv
```

## Cómo Obtener el Listing ID

El `listing-id` es el número largo que aparece en la URL del listing:

```
https://www.airbnb.com.ar/rooms/928978094650118177
                                  ^^^^^^^^^^^^^^^^^^^
                                  Este es el listing-id
```

## Dependencias

```bash
pip install requests
```

## Ejemplos Completos

### Ejemplo 1: Monitoreo de disponibilidad para diciembre 2025

```bash
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 \
    --end 2025-12-31 \
    --guests 2 \
    --listing-name "Cabaña Villa Carlos Paz" \
    --out tmp/diciembre_2025_disponibilidad.csv
```

### Ejemplo 2: Estimación de precios para temporada alta

```bash
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-15 \
    --end 2026-01-10 \
    --guests 4 \
    --fixed-rate 250 \
    --currency USD \
    --listing-name "Cabaña Villa Carlos Paz" \
    --listing-url "https://www.airbnb.com.ar/rooms/928978094650118177" \
    --out tmp/temporada_alta_estimacion.csv
```

### Ejemplo 3: Precios exactos desde archivo manual

```bash
# 1. Crear archivo de precios
cat > tmp/precios_enero.json <<EOF
{
  "2026-01-01": 280.00,
  "2026-01-02": 280.00,
  "2026-01-03": 320.00,
  "2026-01-04": 320.00,
  "2026-01-05": 280.00
}
EOF

# 2. Generar CSV
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2026-01-01 \
    --end 2026-01-05 \
    --guests 2 \
    --pricing-file tmp/precios_enero.json \
    --out tmp/enero_2026_precios.csv
```

## Limitaciones Conocidas

1. **Precios Exactos:** No es posible obtener precios automáticamente de Airbnb sin autenticación completa. Las opciones son:

   - Usar tasa fija estimada
   - Ingresar precios manualmente en JSON
   - Usar herramientas de scraping del HTML (requiere Selenium/Playwright)

2. **Disponibilidad:** Funciona correctamente con el API key público de Airbnb.

3. **Rate Limiting:** Airbnb puede limitar requests si se hacen muchas consultas en poco tiempo.

4. **Cambios en API:** Airbnb puede cambiar sus endpoints o requerir nuevos headers en cualquier momento.

## Solución de Problemas

### Error: "Response not successful: Received status code 400"

El API key público ha expirado o cambió. Necesitas actualizar el header `x-airbnb-api-key` en el script con un valor actual capturado desde las DevTools del navegador.

### Error: "TypeError: 'NoneType' object is not subscriptable"

La respuesta de la API no contiene datos. Posibles causas:

- Listing ID incorrecto
- Listing no existe o fue eliminado
- API key inválido

### Precios No Aparecen

Por diseño, el endpoint de calendario no incluye precios. Usa `--fixed-rate` o `--pricing-file` para incluir precios en el output.

## Futuras Mejoras

- [ ] Integración con Playwright/Selenium para scraping automático de precios desde HTML
- [ ] Soporte para múltiples listings en batch
- [ ] Exportación a formatos adicionales (Excel, JSON)
- [ ] Detección automática de temporadas altas/bajas
- [ ] Comparación de precios históricos
- [ ] Alertas cuando aparecen fechas disponibles

## Referencias

- API GraphQL de Airbnb: `https://www.airbnb.com.ar/api/v3/`
- Persisted query: `PdpAvailabilityCalendar` (calendario de disponibilidad)
- Persisted query: `stayCheckout` (checkout completo - requiere autenticación)
  que se discuten en el chat.

Propósito

Prototipado rápido: código experimental, pruebas unitarias puntuales,
snippets y scripts de diagnóstico que ayudan a validar ideas antes de
integrarlas en el árbol principal del repositorio.

Capturar el historial de la conversación: los archivos aquí contienen
artefactos generados por la conversación (scripts, replays, pequeños
extractores). No se consideran parte del producto final.

Buenas prácticas y recomendaciones

Contenido efímero: trata esta carpeta como temporal. Revisa su contenido
y mueve lo que sea estable a `scripts/` o `tests/` antes de crear un PR.

No automatices producción desde aquí: si algo en `copilot_tests` se vuelve
útil en producción, refactorízalo, añade documentación y tests en la
ubicación adecuada antes de fusionarlo.

Nombres claros: usa nombres de archivo que indiquen propósito y fecha,
p. ej. `tmp_replay_2025-11-08_stays_pdp_sections.py` o

# copilot_tests — área temporal para prototipado

Propósito

Espacio temporal para prototipos y pruebas rápidas (scripts experimentales,
replays y extractores en desarrollo). No contiene artefactos listos para
producción.

Lineamientos

- Mantener el contenido efímero: mover artefactos estables a `scripts/` o
  `tests/` antes de incorporarlos al flujo principal.
- Nombrado claro: usar nombres que indiquen propósito y fecha (p. ej.
  `quick_test_2025-11-08.py`).
- Limpiar periódicamente: revisar y eliminar archivos temporales antes de
  commits importantes.

Integración

Si un script en este directorio debe conservarse, muévalo a `scripts/`,
añada documentación y tests, y cree un PR desde una rama dedicada.

Política de commits

No incluir directamente `copilot_tests` en `main`; promover solo artefactos
comprobados y documentados.
