# 🔒 Sistema Anti-Duplicado de Scraping (48 horas)

## 📋 Descripción General

Se implementó un sistema de control que **previene la ejecución de scrapings duplicados** dentro de una ventana de **48 horas**. El sistema compara la configuración completa de cada ejecución y bloquea automáticamente intentos repetidos con los mismos parámetros.

---

## ✨ Características

### 1. **Detección Inteligente**
El sistema compara **todos** los parámetros de configuración:
- ✅ Nombre de la propiedad
- ✅ Fecha de inicio (check-in)
- ✅ Fecha de fin (check-out)
- ✅ Número de noches
- ✅ Número de huéspedes
- ✅ Plataformas seleccionadas (Airbnb, Booking)

### 2. **Ventana de 48 Horas**
- Solo se previenen duplicados en las **últimas 48 horas**
- Después de 48 horas, la misma configuración puede ejecutarse nuevamente
- El tiempo se calcula desde el timestamp de la ejecución anterior

### 3. **Opción de Forzar Ejecución**
- Checkbox **"🔄 Forzar ejecución"** en la interfaz
- Permite anular el control anti-duplicado cuando sea necesario
- Útil para debugging o cuando se necesita refrescar datos urgentemente

---

## 🏗️ Implementación Técnica

### Archivos Modificados

#### 1. `src/data_manager.py`
Nuevos métodos añadidos a la clase `DataManager`:

```python
def log_scrape_run(self, property_name, start_date, end_date, nights, guests, platforms):
    """Registra una ejecución de scraping exitosa"""
    # Guarda la configuración y timestamp en data/scrape_runs.json

def is_recent_same_run(self, property_name, start_date, end_date, nights, guests, platforms, window_hours=48):
    """Verifica si ya se ejecutó la misma configuración en las últimas window_hours horas"""
    # Retorna True si encuentra una ejecución idéntica dentro de la ventana de tiempo
```

**Archivo de persistencia:** `data/scrape_runs.json`

#### 2. `app.py`
Modificaciones en las funciones:

**`run_scraping()`**
- Nuevo parámetro: `force_run=False`
- Chequeo anti-duplicado antes de iniciar scraping
- Muestra warning detallado si se detecta duplicado
- Registra ejecución exitosa después de guardar resultados

**`render_scraping_interface()`**
- Nuevo checkbox: "🔄 Forzar ejecución"
- Pasa el parámetro `force_run` a la función de scraping

---

## 📊 Formato del Log

El archivo `data/scrape_runs.json` almacena cada ejecución:

```json
[
  {
    "property_name": "Aizeder Eco Container House",
    "start_date": "2025-11-06",
    "end_date": "2025-11-13",
    "nights": 2,
    "guests": 2,
    "platforms": ["airbnb", "booking"],
    "ts": "2025-11-06T16:23:51"
  }
]
```

---

## 🔄 Flujo de Funcionamiento

### Escenario 1: Primera Ejecución
```
Usuario configura scraping → No hay ejecución previa → ✅ Scraping procede → Se registra en log
```

### Escenario 2: Ejecución Duplicada (< 48h)
```
Usuario configura scraping → Se detecta ejecución idéntica < 48h → ⚠️ Warning mostrado → Scraping bloqueado
```

### Escenario 3: Forzar Ejecución
```
Usuario marca "Forzar ejecución" → Control anti-duplicado desactivado → ✅ Scraping procede → Se registra en log
```

### Escenario 4: Después de 48 Horas
```
Usuario configura scraping → Ejecución anterior > 48h → ✅ Scraping procede → Se registra en log
```

---

## 🧪 Testing

Se incluye el script `test_anti_duplicate.py` que verifica:

✅ Test 1: No detecta duplicado cuando no hay ejecuciones previas  
✅ Test 2: Registra correctamente una nueva ejecución  
✅ Test 3: Detecta duplicado con configuración idéntica  
✅ Test 4: No detecta duplicado con noches diferentes  
✅ Test 5: No detecta duplicado con plataformas diferentes  
✅ Test 6: No detecta duplicado con propiedad diferente  

**Ejecutar tests:**
```bash
python test_anti_duplicate.py
```

---

## 📝 Mensaje de Warning

Cuando se detecta un duplicado, el usuario ve:

```
⚠️ Ejecución Duplicada Detectada

Ya existe un scraping con esta configuración para 'Aizeder Eco Container House' 
realizado en las últimas 48 horas.

- Propiedad: Aizeder Eco Container House
- Fechas: 06/11/2025 - 13/11/2025
- Noches: 2
- Huéspedes: 2
- Plataformas: airbnb, booking

Para ejecutarlo de todas formas, marca la opción "Forzar ejecución" y vuelve a intentar.
```

---

## 💡 Ventajas

1. **Ahorro de recursos**: Evita scrapings innecesarios
2. **Protección anti-ban**: Reduce requests repetidos a las plataformas
3. **Control de costos**: Minimiza uso de recursos computacionales
4. **Flexibilidad**: Opción de override cuando sea necesario
5. **Trazabilidad**: Log completo de todas las ejecuciones

---

## 🔧 Configuración

### Cambiar la ventana de tiempo

Por defecto es **48 horas**, pero se puede ajustar modificando el parámetro en `app.py`:

```python
is_recent = data_manager.is_recent_same_run(
    # ... otros parámetros ...
    window_hours=48  # ← Cambiar aquí (ej: 24, 72, etc.)
)
```

### Desactivar completamente

Para desactivar el control (no recomendado):

1. Comentar el bloque de chequeo en `run_scraping()`
2. O siempre marcar "Forzar ejecución"

---

## 📅 Fecha de Implementación

**6 de noviembre de 2025**

---

## ✅ Estado

**✓ Implementado y probado**  
**✓ Tests pasando correctamente**  
**✓ Integrado en UI de Streamlit**
