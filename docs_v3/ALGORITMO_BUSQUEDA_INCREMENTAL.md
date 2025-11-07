# Algoritmo de Búsqueda Incremental de Precios

> **Fecha**: 2025-11-07  
> **Estado**: Diseño fundamental V3

---

## 🎯 Problema

**No es posible obtener directamente el precio de UNA noche** porque:
- Muchos establecimientos tienen **mínimo de noches** (ej: 2-3 noches)
- La búsqueda de 1 sola noche puede dar "no disponible" aunque haya disponibilidad
- Necesitamos **deducir el precio por noche** a partir de búsquedas de múltiples noches

---

## 💡 Solución: Búsqueda Incremental 3→2→1

### Algoritmo Principal

Para cada **fecha inicial** (ej: `01/02/2026`):

```
┌─────────────────────────────────────────────────────┐
│ PASO 0: Verificación de Caché                      │
├─────────────────────────────────────────────────────┤
│ ¿Existe precio para fecha_inicial en BD?           │
│ ¿El precio fue scrapeado hace < 24h (caché)?       │
│                                                     │
│ SI → OMITIR esta fecha (usar dato existente)       │
│ NO → Continuar con PASO 1                          │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ PASO 1: Búsqueda de 3 noches                       │
├─────────────────────────────────────────────────────┤
│ check_in  = fecha_inicial                          │
│ check_out = fecha_inicial + 3 días                 │
│                                                     │
│ Scrapear URL con estos parámetros                  │
│                                                     │
│ RESULTADO:                                          │
│ • Éxito (precio_total > 0)                          │
│   → precio_por_noche = precio_total / 3             │
│   → GUARDAR precio para 3 fechas:                   │
│      - fecha_inicial                                │
│      - fecha_inicial + 1                            │
│      - fecha_inicial + 2                            │
│   → SALTAR a fecha_inicial + 3 (siguiente búsqueda) │
│                                                     │
│ • Fallo (no disponible / error)                     │
│   → Continuar con PASO 2                            │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ PASO 2: Búsqueda de 2 noches                       │
├─────────────────────────────────────────────────────┤
│ check_in  = fecha_inicial                          │
│ check_out = fecha_inicial + 2 días                 │
│                                                     │
│ RESULTADO:                                          │
│ • Éxito (precio_total > 0)                          │
│   → precio_por_noche = precio_total / 2             │
│   → GUARDAR precio para 2 fechas:                   │
│      - fecha_inicial                                │
│      - fecha_inicial + 1                            │
│   → SALTAR a fecha_inicial + 2 (siguiente búsqueda) │
│                                                     │
│ • Fallo (no disponible / error)                     │
│   → Continuar con PASO 3                            │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ PASO 3: Búsqueda de 1 noche                        │
├─────────────────────────────────────────────────────┤
│ check_in  = fecha_inicial                          │
│ check_out = fecha_inicial + 1 día                  │
│                                                     │
│ RESULTADO:                                          │
│ • Éxito (precio_total > 0)                          │
│   → precio_por_noche = precio_total                 │
│   → GUARDAR precio para 1 fecha:                    │
│      - fecha_inicial                                │
│   → SALTAR a fecha_inicial + 1 (siguiente búsqueda) │
│                                                     │
│ • Fallo (no disponible / error)                     │
│   → Continuar con PASO 4                            │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ PASO 4: Marcar como OCUPADO                        │
├─────────────────────────────────────────────────────┤
│ No hay disponibilidad para esta fecha              │
│                                                     │
│ GUARDAR precio = $0 para fecha_inicial             │
│ (indica ocupación/no disponibilidad)                │
│                                                     │
│ SALTAR a fecha_inicial + 1 (siguiente búsqueda)    │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Ejemplo Concreto

### Escenario: Scraping 01/02/2026 → 10/02/2026 (10 días)

```
Fecha: 01/02/2026
├─ Caché: NO existe → Buscar
├─ 3 noches (01→04): ✅ Éxito → $450 total → $150/noche
├─ Guardar: 01/02, 02/02, 03/02 → $150 cada una
└─ Saltar a: 04/02/2026

Fecha: 04/02/2026
├─ Caché: NO existe → Buscar
├─ 3 noches (04→07): ❌ Fallo (mínimo 4 noches)
├─ 2 noches (04→06): ✅ Éxito → $340 total → $170/noche
├─ Guardar: 04/02, 05/02 → $170 cada una
└─ Saltar a: 06/02/2026

Fecha: 06/02/2026
├─ Caché: NO existe → Buscar
├─ 3 noches (06→09): ❌ Fallo
├─ 2 noches (06→08): ❌ Fallo
├─ 1 noche (06→07):  ✅ Éxito → $200 total → $200/noche
├─ Guardar: 06/02 → $200
└─ Saltar a: 07/02/2026

Fecha: 07/02/2026
├─ Caché: NO existe → Buscar
├─ 3 noches (07→10): ❌ Fallo
├─ 2 noches (07→09): ❌ Fallo
├─ 1 noche (07→08):  ❌ Fallo
├─ OCUPADO: Guardar $0
└─ Saltar a: 08/02/2026

Fecha: 08/02/2026
├─ Caché: NO existe → Buscar
├─ 3 noches (08→11): ✅ Éxito → $600 total → $200/noche
├─ Guardar: 08/02, 09/02, 10/02 → $200 cada una
└─ FIN (todas las fechas cubiertas)

RESULTADO FINAL:
┌───────────┬────────────┬──────────────┐
│   Fecha   │   Precio   │    Estado    │
├───────────┼────────────┼──────────────┤
│ 01/02/26  │  $150.00   │  Disponible  │
│ 02/02/26  │  $150.00   │  Disponible  │
│ 03/02/26  │  $150.00   │  Disponible  │
│ 04/02/26  │  $170.00   │  Disponible  │
│ 05/02/26  │  $170.00   │  Disponible  │
│ 06/02/26  │  $200.00   │  Disponible  │
│ 07/02/26  │    $0.00   │  🔒 OCUPADO  │
│ 08/02/26  │  $200.00   │  Disponible  │
│ 09/02/26  │  $200.00   │  Disponible  │
│ 10/02/26  │  $200.00   │  Disponible  │
└───────────┴────────────┴──────────────┘

BÚSQUEDAS REALIZADAS: 5 (en lugar de 10)
EFICIENCIA: 50% menos requests
```

---

## 🔑 Características Clave

### 1. Optimización por Caché
- **Evita búsquedas innecesarias**: Si una fecha ya tiene precio reciente (< 24h), se omite
- **Reduce carga en plataformas**: Menos requests = menos bloqueos anti-bot
- **Mejora performance**: Scraping más rápido

### 2. Eficiencia de Búsqueda
- **Saltos inteligentes**: Cuando 3 noches tiene éxito, saltamos 3 fechas (no 1)
- **Menos requests**: En el ejemplo, 5 búsquedas en lugar de 10
- **Cobertura completa**: Todas las fechas quedan registradas

### 3. Normalización de Precios
```python
# Ejemplo de normalización
precio_total = 450.00  # USD por 3 noches
noches = 3
precio_por_noche = precio_total / noches  # 150.00 USD/noche

# Guardar para cada fecha individual:
for i in range(noches):
    fecha = check_in + timedelta(days=i)
    guardar_precio(
        fecha=fecha,
        precio=precio_por_noche,
        moneda='USD',
        noches_scrapeadas=noches,  # metadata
        precio_total_original=precio_total  # trazabilidad
    )
```

### 4. Manejo de Ocupación
```python
# Cuando todo falla (3, 2, 1 noches)
if not disponible:
    guardar_precio(
        fecha=fecha_inicial,
        precio=0.00,  # Indica ocupación
        moneda='USD',
        estado='OCUPADO',
        metadata={'intentos': [3, 2, 1], 'todos_fallaron': True}
    )
```

---

## 🏗️ Arquitectura de Implementación

### Componentes Necesarios

```
┌──────────────────────────────────────────────────────┐
│ ScraperScheduler                                     │
│ ├─ get_date_range_to_scrape(start, end, url)        │
│ │  └─ Retorna: List[fecha_inicial] (filtra cache)   │
│ ├─ scrape_date_incremental(url, fecha_inicial)      │
│ │  ├─ try_scrape_nights(url, fecha, nights=3)       │
│ │  ├─ try_scrape_nights(url, fecha, nights=2)       │
│ │  ├─ try_scrape_nights(url, fecha, nights=1)       │
│ │  └─ mark_as_occupied(url, fecha)                  │
│ └─ normalize_and_save(precio_total, noches, fecha)  │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ OrchestratorV3                                       │
│ └─ scrape_establishment(url, check_in, check_out)   │
│    (sin cambios en interfaz, solo parámetros)       │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ Robots (Airbnb/Booking/Expedia)                     │
│ └─ scrape(url, check_in, check_out)                 │
│    └─ Return: {precio_total, noches, moneda, ...}   │
└──────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────┐
│ DatabaseAdapter                                      │
│ ├─ should_scrape_date(url_id, fecha, cache_hours)   │
│ │  └─ Check if fecha needs scraping (cache check)   │
│ ├─ save_price_per_night(url_id, fecha, precio, ...)│
│ │  └─ Save individual night price with metadata     │
│ └─ mark_date_occupied(url_id, fecha)                │
│    └─ Save $0 price with 'OCUPADO' status           │
└──────────────────────────────────────────────────────┘
```

---

## 📝 Modelo de Datos

### Extensión de Schema

```sql
-- Tabla principal (ya existe)
CREATE TABLE precios (
    id_precio INTEGER PRIMARY KEY,
    id_plataforma_url INTEGER,
    fecha_noche DATE,
    precio_noche REAL,
    moneda TEXT,
    timestamp_captura DATETIME,
    
    -- NUEVOS CAMPOS:
    noches_scrapeadas INTEGER,       -- 3, 2, 1, o NULL si precio directo
    precio_total_original REAL,      -- Precio total antes de división
    estado TEXT,                     -- 'DISPONIBLE' o 'OCUPADO'
    metadatos_scraping TEXT,         -- JSON con info adicional
    
    FOREIGN KEY (id_plataforma_url) REFERENCES plataforma_urls(id_plataforma_url)
);

CREATE INDEX idx_precios_fecha_url ON precios(id_plataforma_url, fecha_noche);
CREATE INDEX idx_precios_estado ON precios(estado);
```

### Ejemplo de Registro

```json
// Precio exitoso (3 noches)
{
    "id_precio": 1234,
    "id_plataforma_url": 5,
    "fecha_noche": "2026-02-01",
    "precio_noche": 150.00,
    "moneda": "USD",
    "timestamp_captura": "2025-11-07 21:00:00",
    "noches_scrapeadas": 3,
    "precio_total_original": 450.00,
    "estado": "DISPONIBLE",
    "metadatos_scraping": {
        "intento": "3_noches",
        "check_in": "2026-02-01",
        "check_out": "2026-02-04",
        "fuente": "dom",
        "quality": 0.95
    }
}

// Precio ocupado
{
    "id_precio": 1235,
    "id_plataforma_url": 5,
    "fecha_noche": "2026-02-07",
    "precio_noche": 0.00,
    "moneda": "USD",
    "timestamp_captura": "2025-11-07 21:02:00",
    "noches_scrapeadas": null,
    "precio_total_original": null,
    "estado": "OCUPADO",
    "metadatos_scraping": {
        "intentos_fallidos": ["3_noches", "2_noches", "1_noche"],
        "razon": "no_disponible_todas_duraciones"
    }
}
```

---

## 🧪 Casos de Prueba

### Test 1: Disponibilidad completa con 3 noches
```python
# Input
fecha_inicial = date(2026, 2, 1)
url = "https://airbnb.com/rooms/123"

# Búsqueda 3 noches: ✅ $450 total
# Expected Output
assert len(precios_guardados) == 3
assert all(p.precio_noche == 150.0 for p in precios_guardados)
assert all(p.estado == 'DISPONIBLE' for p in precios_guardados)
```

### Test 2: Mínimo 2 noches
```python
# Input
fecha_inicial = date(2026, 2, 1)

# Búsqueda 3 noches: ❌ Error
# Búsqueda 2 noches: ✅ $340 total
# Expected Output
assert len(precios_guardados) == 2
assert all(p.precio_noche == 170.0 for p in precios_guardados)
assert all(p.noches_scrapeadas == 2 for p in precios_guardados)
```

### Test 3: Totalmente ocupado
```python
# Input
fecha_inicial = date(2026, 2, 1)

# Búsqueda 3 noches: ❌ Error
# Búsqueda 2 noches: ❌ Error
# Búsqueda 1 noche:  ❌ Error
# Expected Output
assert len(precios_guardados) == 1
assert precios_guardados[0].precio_noche == 0.0
assert precios_guardados[0].estado == 'OCUPADO'
```

### Test 4: Respeto de caché
```python
# Setup: fecha_inicial ya tiene precio reciente (< 24h)
db.save_price(url_id, date(2026, 2, 1), 150.0, timestamp=now() - timedelta(hours=12))

# Input
fecha_inicial = date(2026, 2, 1)

# Expected Output
assert not should_scrape_date(url_id, fecha_inicial)
assert num_requests == 0  # No se hace ninguna búsqueda
```

---

## 🎯 Ventajas del Algoritmo

### 1. **Eficiencia**
- 50-70% menos requests vs scraping individual por noche
- Menor carga en servidores objetivo
- Menor riesgo de bloqueo anti-bot

### 2. **Cobertura Completa**
- Todas las fechas quedan registradas
- No hay "huecos" en los datos
- Ocupación explícita ($0) vs ausencia de datos

### 3. **Respeto de Restricciones**
- Maneja mínimos de noches de cada propiedad
- Se adapta automáticamente a políticas diferentes
- No fuerza búsquedas inválidas

### 4. **Trazabilidad**
- Cada precio sabe de qué búsqueda proviene (metadata)
- Se puede recalcular/validar precio_por_noche
- Auditoría completa de intentos fallidos

### 5. **Caché Inteligente**
- Evita re-scraping innecesario
- Prioriza datos frescos sobre requests
- Configurable por caso de uso

---

## 🚀 Plan de Implementación

### Fase 1: Core Engine (2-3 horas)
- [ ] `scrape_date_incremental()` en scheduler
- [ ] `try_scrape_nights(nights=N)` genérico
- [ ] Normalización precio_total → precio_por_noche
- [ ] Lógica de saltos (fecha_inicial + noches_exitosas)

### Fase 2: Cache System (1 hora)
- [ ] `should_scrape_date(url_id, fecha, cache_hours)`
- [ ] Filtrado de fechas antes de scraping
- [ ] Tests de caché

### Fase 3: Database (1-2 horas)
- [ ] Extender schema con nuevos campos
- [ ] Métodos de guardado con metadata
- [ ] Queries para analítica de ocupación

### Fase 4: UI Integration (1 hora)
- [ ] Actualizar UI de scraping para mostrar progreso por fecha
- [ ] Visualización de ocupación ($0 vs disponible)
- [ ] Tabla con columna "Noches Scrapeadas"

### Fase 5: Testing (2 horas)
- [ ] Tests unitarios del algoritmo
- [ ] Tests de integración con robots
- [ ] Validación con URLs reales

---

## 📚 Referencias

- [FASE_2_INGESTA_Y_SCRAPING.md](FASE_2_INGESTA_Y_SCRAPING.md): Metodologías por plataforma
- [SDK_V3_README.md](../SDK_V3_README.md): Contratos de robots y parsers
- [FASE_3_PERSISTENCIA_Y_NORMALIZACION.md](FASE_3_PERSISTENCIA_Y_NORMALIZACION.md): Normalización de datos

---

**Próximo paso**: Implementar `scrape_date_incremental()` en `scheduler_v3.py`
