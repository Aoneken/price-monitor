# 🚀 Sistema de Búsqueda Incremental - Implementado

> **Fecha**: 2025-11-07  
> **Estado**: ✅ **IMPLEMENTADO Y LISTO PARA PRUEBAS**  
> **Branch**: v3  
> **Commit**: 8e17eec

---

## 📋 Resumen Ejecutivo

### ❌ Problema Identificado

El sistema anterior intentaba obtener el **precio de 1 noche individual** para cada fecha, lo que causaba:

1. **Fallos constantes**: Muchos establecimientos tienen **mínimo de 2-3 noches**
2. **Datos incompletos**: Búsquedas de 1 noche daban "no disponible" aunque había disponibilidad
3. **Ineficiencia**: 1 request por fecha = muchos requests
4. **Logs llenos de errores**: Timeout, PRICE_NOT_FOUND, etc.

**Ejemplo del problema**:
```
Búsqueda: 01/02/26 → 02/02/26 (1 noche)
Resultado: ❌ ERROR - "Mínimo 2 noches"

Búsqueda: 02/02/26 → 03/02/26 (1 noche)
Resultado: ❌ ERROR - "Mínimo 2 noches"

Búsqueda: 03/02/26 → 04/02/26 (1 noche)
Resultado: ❌ ERROR - "Mínimo 2 noches"

→ 3 requests, 0 datos obtenidos
```

---

### ✅ Solución Implementada: Algoritmo Incremental 3→2→1

El nuevo sistema:

1. **Busca primero 3 noches** → Si éxito, divide precio_total / 3 = precio_por_noche
2. **Si falla, busca 2 noches** → Si éxito, divide / 2
3. **Si falla, busca 1 noche** → Precio directo
4. **Si todo falla** → Marca fecha como **OCUPADA** ($0)
5. **Saltos inteligentes**: Si 3 noches tiene éxito, salta +3 días (no +1)

**Mismo ejemplo con nuevo algoritmo**:
```
Búsqueda: 01/02/26 → 04/02/26 (3 noches)
Resultado: ✅ $450 total → $150/noche
Guardar: 01/02, 02/02, 03/02 → $150 c/u

→ 1 request, 3 fechas resueltas (eficiencia 300%)
```

---

## 🔧 Componentes Implementados

### 1. **Base de Datos** (ACTUALIZADA)

```sql
-- Nuevos campos en tabla Precios
ALTER TABLE Precios ADD COLUMN precio_total_original REAL;
ALTER TABLE Precios ADD COLUMN moneda TEXT DEFAULT 'USD';
ALTER TABLE Precios ADD COLUMN metadatos_scraping TEXT;  -- JSON

-- Campos existentes reutilizados
noches_encontradas INTEGER;  -- 1, 2, o 3
esta_ocupado BOOLEAN;        -- TRUE si precio = 0
```

### 2. **DatabaseAdapter** (EXTENDIDO)

Nuevos métodos:

```python
# Verificar si fecha necesita scraping (caché)
db.should_scrape_date(url_id, fecha, cache_hours=24)

# Guardar precio normalizado con metadata
db.save_price_per_night(
    url_id, fecha, precio, moneda,
    noches_scrapeadas=3,
    precio_total_original=450.00,
    metadatos={'intento': '3_noches', 'fuente': 'dom'}
)

# Marcar fecha como ocupada
db.mark_date_occupied(url_id, fecha, ['3_noches', '2_noches', '1_noche'])
```

### 3. **Scheduler Incremental** (NUEVO)

Archivo: `scripts/scheduler_incremental_v3.py`

```python
from scripts.scheduler_incremental_v3 import IncrementalScraperScheduler

scheduler = IncrementalScraperScheduler(cache_hours=24)

stats = scheduler.scrape_all_urls_date_range(
    start_date=date(2026, 2, 1),
    end_date=date(2026, 2, 10),
    platform_filter='Booking'  # Opcional
)
```

---

## 🎯 Cómo Usar el Nuevo Sistema

### Opción 1: CLI (Recomendado para testing)

```bash
# Scraping de 7 días para todas las plataformas
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07

# Solo Booking
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07 \
  --platform Booking

# Solo un establecimiento
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07 \
  --establishment 2

# Sin caché (testing)
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07 \
  --cache-hours 0

# Modo visible (debugging)
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07 \
  --no-headless
```

### Opción 2: Script Python

```python
from datetime import date, timedelta
from scripts.scheduler_incremental_v3 import IncrementalScraperScheduler

# Crear scheduler
scheduler = IncrementalScraperScheduler(
    cache_hours=24,
    headless=True
)

# Definir rango
start = date.today() + timedelta(days=7)
end = start + timedelta(days=30)

# Ejecutar
stats = scheduler.scrape_all_urls_date_range(
    start_date=start,
    end_date=end,
    platform_filter='Airbnb'
)

# Resultados
print(f"Fechas resueltas: {stats['total_dates']}")
print(f"Requests: {stats['requests_made']}")
print(f"Eficiencia: {stats['efficiency']:.1f}%")
```

### Opción 3: Test Rápido

```bash
# Script de prueba incluido
python test_incremental_quick.py
```

---

## 📊 Output y Logs

### Logs Estructurados

El scheduler genera logs detallados en `logs/scheduler_v3.log`:

```
============================================================
Scraping Booking URL 5
Rango: 2026-02-01 → 2026-02-07
============================================================

→ Procesando fecha: 2026-02-01
  Intentando 3 noches: 2026-02-01 → 2026-02-04
  ✓ 3 noches: $150.0/noche (total: $450.0)
  ✓ 3 noches guardadas (3/3)

→ Procesando fecha: 2026-02-04
  ⊙ Fecha 2026-02-04: en caché, omitiendo

→ Procesando fecha: 2026-02-05
  Intentando 3 noches: 2026-02-05 → 2026-02-08
  ✗ 3 noches: PRICE_NOT_FOUND
  Intentando 2 noches: 2026-02-05 → 2026-02-07
  ✓ 2 noches: $170.0/noche (total: $340.0)
  ✓ 2 noches guardadas (2/2)

→ Procesando fecha: 2026-02-07
  Intentando 3 noches: 2026-02-07 → 2026-02-10
  ✗ 3 noches: PRICE_NOT_FOUND
  Intentando 2 noches: 2026-02-07 → 2026-02-09
  ✗ 2 noches: PRICE_NOT_FOUND
  Intentando 1 noche: 2026-02-07 → 2026-02-08
  ✗ 1 noche: PRICE_NOT_FOUND
  🔒 Todas las búsquedas fallaron → Marcando como OCUPADO

============================================================
RESUMEN - Booking URL 5
============================================================
Fechas totales:     7
En caché:           1
Éxitos 3 noches:    1 (3 fechas)
Éxitos 2 noches:    1 (2 fechas)
Éxitos 1 noche:     0
Ocupadas:           1
Requests hechos:    7
Eficiencia:         85.7% (fechas/requests)
============================================================
```

### Estadísticas Globales

Al final del scraping:

```
######################################################################
# RESUMEN GLOBAL
######################################################################
URLs procesadas:    3
Fechas totales:     21
En caché:           0
Éxitos 3 noches:    4 → 12 fechas
Éxitos 2 noches:    3 → 6 fechas
Éxitos 1 noche:     2 → 2 fechas
Ocupadas:           1
Requests totales:   10
Eficiencia global:  210.0%
######################################################################
```

**Eficiencia**: `(fechas_resueltas / requests) * 100`

- Sin algoritmo: ~21 requests (1 por fecha)
- Con algoritmo: 10 requests
- **Ahorro: 52%**

---

## 🗄️ Datos en Base de Datos

### Tabla Precios - Ejemplo de Registros

```sql
SELECT 
    fecha_noche,
    precio_base,
    esta_ocupado,
    noches_encontradas,
    precio_total_original,
    moneda,
    metadatos_scraping
FROM Precios
WHERE id_plataforma_url = 5
  AND fecha_noche >= '2026-02-01'
ORDER BY fecha_noche;
```

Resultado:
```
fecha_noche  | precio_base | ocupado | noches_encontradas | precio_total | moneda | metadatos
-------------|-------------|---------|-------------------|--------------|--------|----------------------------------
2026-02-01   | 150.00      | 0       | 3                 | 450.00       | USD    | {"intento":"3_noches","fuente":"dom"}
2026-02-02   | 150.00      | 0       | 3                 | 450.00       | USD    | {"intento":"3_noches","fuente":"dom"}
2026-02-03   | 150.00      | 0       | 3                 | 450.00       | USD    | {"intento":"3_noches","fuente":"dom"}
2026-02-04   | 170.00      | 0       | 2                 | 340.00       | USD    | {"intento":"2_noches","fuente":"dom"}
2026-02-05   | 170.00      | 0       | 2                 | 340.00       | USD    | {"intento":"2_noches","fuente":"dom"}
2026-02-06   | 200.00      | 0       | 1                 | 200.00       | USD    | {"intento":"1_noche","fuente":"dom"}
2026-02-07   | 0.00        | 1       | NULL              | NULL         | USD    | {"intentos_fallidos":["3","2","1"],"razon":"no_disponible"}
```

**Interpretación**:
- **Fechas 01-03**: Precio obtenido de búsqueda de 3 noches ($150/noche)
- **Fechas 04-05**: Precio obtenido de búsqueda de 2 noches ($170/noche)
- **Fecha 06**: Precio obtenido de búsqueda de 1 noche ($200/noche)
- **Fecha 07**: **OCUPADO** - ninguna búsqueda tuvo éxito

---

## ✅ Ventajas del Nuevo Sistema

| Aspecto | Sistema Anterior | Sistema Nuevo |
|---------|------------------|---------------|
| **Requests por 10 días** | ~10 (1 por día) | ~3-5 (saltos inteligentes) |
| **Eficiencia** | 100% (1 fecha/request) | 200-300% (2-3 fechas/request) |
| **Cobertura** | Parcial (muchos fallos) | Completa (todas las fechas) |
| **Ocupación** | Desconocida (fallo = dato perdido) | Explícita ($0 en BD) |
| **Mínimo noches** | No respeta | Respeta automáticamente |
| **Trazabilidad** | Limitada | Completa (metadata JSON) |
| **Logs** | Confusos (muchos errores) | Claros (éxito por nivel) |

---

## 🧪 Testing Sugerido

### Test 1: Prueba Básica (7 días, 1 plataforma)

```bash
# Booking es la más estable
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-07 \
  --platform Booking \
  --cache-hours 0 \
  --no-headless
```

**Esperado**:
- Eficiencia > 150%
- Logs claros con intentos 3→2→1
- BD con `noches_encontradas` llenado correctamente

### Test 2: Prueba de Caché

```bash
# Primera ejecución
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-03 \
  --platform Booking

# Segunda ejecución (inmediata)
python scripts/scheduler_incremental_v3.py \
  --start-date 2026-02-01 \
  --end-date 2026-02-03 \
  --platform Booking
```

**Esperado**:
- Segunda ejecución: todas las fechas "en caché"
- 0 requests en segunda ejecución

### Test 3: Prueba de Ocupación

```bash
# Buscar fecha muy lejana (probablemente ocupada)
python scripts/scheduler_incremental_v3.py \
  --start-date 2027-12-24 \
  --end-date 2027-12-31 \
  --platform Airbnb
```

**Esperado**:
- Algunas fechas marcadas como OCUPADAS ($0)
- Metadata con `intentos_fallidos: [3, 2, 1]`

---

## 📚 Documentación Completa

- **[ALGORITMO_BUSQUEDA_INCREMENTAL.md](docs_v3/ALGORITMO_BUSQUEDA_INCREMENTAL.md)**: Diseño detallado con diagramas
- **[scheduler_incremental_v3.py](scripts/scheduler_incremental_v3.py)**: Código fuente completo
- **[database_adapter.py](src/persistence/database_adapter.py)**: Métodos de BD extendidos

---

## 🚦 Próximos Pasos

1. **Ejecutar test básico** con el comando sugerido arriba
2. **Revisar logs** en `logs/scheduler_v3.log`
3. **Verificar BD** con queries SQL de ejemplo
4. **Validar eficiencia**: Debe ser > 150%
5. **Reportar resultados**: Éxitos, fallos, observaciones

---

## ❓ FAQ

**P: ¿El scheduler anterior sigue funcionando?**  
R: Sí, `scheduler_v3.py` sigue disponible. El incremental es `scheduler_incremental_v3.py`.

**P: ¿Puedo usar ambos?**  
R: Sí, pero el incremental es más eficiente. Recomendamos migrar.

**P: ¿Qué pasa si cambio cache_hours?**  
R: Con `cache_hours=0` se desactiva el caché (útil para testing). Con `24` (default) se omiten fechas scrapeadas hace < 24h.

**P: ¿Por qué algunos precios son $0?**  
R: Precio $0 + `esta_ocupado=TRUE` significa que **no hay disponibilidad** para esa fecha (probado con 3, 2 y 1 noches).

**P: ¿Cómo sé qué búsqueda tuvo éxito?**  
R: Campo `noches_encontradas`: 3 = búsqueda de 3 noches, 2 = 2 noches, 1 = 1 noche, NULL = ocupado.

---

## 🎉 Conclusión

El **algoritmo de búsqueda incremental** resuelve el problema fundamental de obtener precios por noche respetando los mínimos de estadía de cada establecimiento.

**Resultado esperado**:
- ✅ Menos errores en logs
- ✅ Mayor cobertura de datos
- ✅ Mejor eficiencia (menos requests)
- ✅ Ocupación explícita (no ambigüedad)

**Listo para probar!** 🚀
