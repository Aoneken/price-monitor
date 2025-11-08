# Ejemplo de Uso: Monitoreo de Precios para Villa Carlos Paz

Este ejemplo demuestra cómo usar `get_prices_simple.py` para monitorear disponibilidad y precios de un establecimiento en Airbnb.

## Datos del Establecimiento

- **Nombre:** Villa Carlos Paz Property
- **Listing ID:** 928978094650118177
- **URL:** https://www.airbnb.com.ar/rooms/928978094650118177
- **Ubicación:** Villa Carlos Paz, Córdoba, Argentina

## Caso de Uso 1: Monitoreo de Disponibilidad (Solo)

Objetivo: Ver qué fechas están disponibles en diciembre 2025.

```bash
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 \
    --end 2025-12-31 \
    --guests 2 \
    --listing-name "Villa Carlos Paz Property" \
    --out tmp/vcp_diciembre_disponibilidad.csv
```

**Resultado:** CSV con columnas de disponibilidad (available, bookable, minNights, maxNights) pero sin precios.

## Caso de Uso 2: Estimación Rápida con Tasa Fija

Objetivo: Estimar ingresos potenciales asumiendo $200 USD por noche.

```bash
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 \
    --end 2025-12-31 \
    --guests 2 \
    --fixed-rate 200 \
    --listing-name "Villa Carlos Paz Property" \
    --listing-url "https://www.airbnb.com.ar/rooms/928978094650118177" \
    --out tmp/vcp_diciembre_estimacion.csv
```

**Resultado:** CSV con disponibilidad + precio fijo de $200 USD aplicado a todas las fechas bookable.

**Análisis:**

```bash
# Contar noches disponibles
grep -c '"True".*"True".*"True".*"True".*"200.00"' tmp/vcp_diciembre_estimacion.csv

# Calcular ingreso potencial (ejemplo: 20 noches disponibles × $200)
# = $4,000 USD potenciales
```

## Caso de Uso 3: Precios Exactos con Entrada Manual

Objetivo: Crear tabla precisa después de consultar manualmente Airbnb.

### Paso 1: Visitar Airbnb y Anotar Precios

1. Ir a https://www.airbnb.com.ar/rooms/928978094650118177
2. Seleccionar fechas y 2 huéspedes
3. Anotar precios por noche mostrados en el calendario

### Paso 2: Crear Archivo JSON con Precios

```bash
cat > tmp/vcp_precios_diciembre.json <<'EOF'
{
  "2025-12-01": 180.00,
  "2025-12-02": 180.00,
  "2025-12-03": 180.00,
  "2025-12-04": 180.00,
  "2025-12-05": 0.00,
  "2025-12-06": 0.00,
  "2025-12-07": 180.00,
  "2025-12-08": 180.00,
  "2025-12-09": 180.00,
  "2025-12-10": 195.50,
  "2025-12-11": 195.50,
  "2025-12-12": 220.00,
  "2025-12-13": 220.00,
  "2025-12-14": 250.00,
  "2025-12-15": 250.00,
  "2025-12-16": 195.50,
  "2025-12-17": 195.50,
  "2025-12-18": 195.50,
  "2025-12-19": 220.00,
  "2025-12-20": 220.00,
  "2025-12-21": 250.00,
  "2025-12-22": 250.00,
  "2025-12-23": 280.00,
  "2025-12-24": 280.00,
  "2025-12-25": 280.00,
  "2025-12-26": 280.00,
  "2025-12-27": 280.00,
  "2025-12-28": 280.00,
  "2025-12-29": 250.00,
  "2025-12-30": 250.00,
  "2025-12-31": 320.00
}
EOF
```

### Paso 3: Generar CSV con Precios Exactos

```bash
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 \
    --end 2025-12-31 \
    --guests 2 \
    --pricing-file tmp/vcp_precios_diciembre.json \
    --listing-name "Villa Carlos Paz Property" \
    --listing-url "https://www.airbnb.com.ar/rooms/928978094650118177" \
    --currency USD \
    --out tmp/vcp_diciembre_precios_exactos.csv
```

**Resultado:** CSV con disponibilidad + precios exactos por fecha.

### Paso 4: Análisis de Datos

```bash
# Ver header con metadata
head -7 tmp/vcp_diciembre_precios_exactos.csv

# Ver días con mayor precio
grep '280.00\|320.00' tmp/vcp_diciembre_precios_exactos.csv

# Calcular ingreso total del mes (manualmente o con script Python)
# Suma de (pricePerNight × bookable) para todas las fechas
```

## Caso de Uso 4: Comparación de Múltiples Periodos

Para analizar tendencias de precios entre temporadas:

```bash
# Diciembre (temporada alta)
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 --end 2025-12-31 \
    --guests 2 --fixed-rate 220 \
    --out tmp/vcp_diciembre.csv

# Enero (pico temporada)
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2026-01-01 --end 2026-01-31 \
    --guests 2 --fixed-rate 280 \
    --out tmp/vcp_enero.csv

# Febrero (temporada baja)
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2026-02-01 --end 2026-02-28 \
    --guests 2 --fixed-rate 150 \
    --out tmp/vcp_febrero.csv
```

Luego consolidar en Excel o script Python para análisis comparativo.

## Caso de Uso 5: Monitoreo de Cambios en Disponibilidad

Para detectar cuándo se liberan fechas bloqueadas:

```bash
# Ejecutar semanalmente
FECHA=$(date +%Y-%m-%d)
python3 scripts/get_prices_simple.py \
    --listing-id 928978094650118177 \
    --start 2025-12-01 \
    --end 2026-03-31 \
    --guests 2 \
    --listing-name "Villa Carlos Paz Property" \
    --out "tmp/vcp_snapshot_$FECHA.csv"

# Comparar con snapshot anterior
diff tmp/vcp_snapshot_2025-11-01.csv tmp/vcp_snapshot_2025-11-08.csv | \
    grep 'bookable' | \
    grep -E '(False.*True|True.*False)'
```

## Tips para Obtención Manual de Precios

1. **Usar Modo Incógnito:** Airbnb puede mostrar precios diferentes según tu historial.

2. **Verificar Número de Huéspedes:** Los precios cambian según cantidad de huéspedes.

3. **Considerar Servicios Incluidos:** El precio por noche no incluye:

   - Tarifa de servicio de Airbnb
   - Tarifa de limpieza (una vez por reserva)
   - Impuestos

4. **Capturar Screenshots:** Para auditoría futura.

5. **Automatizar con Selenium (Avanzado):**
   ```python
   # Próxima mejora: script que capture precios del DOM
   from selenium import webdriver
   # ... navegar, extraer precios del calendario HTML
   ```

## Estructura del CSV Final

```
# Metadata (7 líneas de comentarios)
date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,notes
"2025-12-01","True","True","True","True","2","15","180.00","USD",""
"2025-12-02","True","True","True","True","2","15","180.00","USD",""
...
```

**Columnas clave:**

- `date`: Fecha (YYYY-MM-DD)
- `bookable`: Si la fecha es reservable (`True`/`False`)
- `minNights`: Mínimo de noches requeridas
- `pricePerNight`: Precio por noche (vacío si no disponible)
- `currency`: Moneda (USD, ARS, etc.)

## Próximos Pasos

1. Importar CSV a Excel/Google Sheets para análisis visual
2. Crear gráficos de disponibilidad y precios
3. Calcular ingresos proyectados por mes
4. Comparar con competencia (otros listings cercanos)
5. Ajustar precios según demanda observada
