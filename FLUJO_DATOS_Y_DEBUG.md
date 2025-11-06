# 📊 Flujo de Datos y Archivos Debug - Explicación Completa

## 🎯 Resumen Ejecutivo

**Lo más importante:** Los archivos debug (HTML/PNG) **NO** se usan para generar la base de datos. Son **completamente independientes** y solo sirven para troubleshooting.

---

## 🔄 Flujo Real del Sistema

### 1️⃣ **Scraping en Tiempo Real** (Lo que SÍ ocurre)

```
┌─────────────┐
│   Usuario   │
│ inicia      │
│ scraping    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  Streamlit app.py                           │
│  - Configura fechas                         │
│  - Selecciona plataformas                   │
│  - Llama a scrapers                         │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  Scraper (Airbnb/Booking)                   │
│  1. Abre navegador Playwright               │
│  2. Navega a la URL de la propiedad         │
│  3. Extrae precio del HTML EN MEMORIA       │ ← CLAVE: En memoria, no de archivo
│  4. Cierra navegador                        │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  DataManager                                │
│  - Recibe datos de precio                  │
│  - Los agrega a CSV                         │
│  - data/price_history.csv                   │
└─────────────────────────────────────────────┘
```

**Datos guardados directamente:**
```csv
platform,checkin,checkout,price_usd,guests,scraped_at,url,property_name
Airbnb,2025-11-06,2025-11-08,150.00,2,2025-11-06T14:30:00,...,Aizeder Eco Container
Booking,2025-11-06,2025-11-08,155.00,2,2025-11-06T14:32:00,...,Aizeder Eco Container
```

---

## 🐛 Archivos Debug (Opcionales y Separados)

### ¿Cuándo se generan?

**Solo se crean archivos debug cuando:**

1. **`debug_first=True`** en `scrape_date_range()` (actualmente FALSE en app.py)
2. **O cuando NO se encuentra precio** (para debugging automático)

### ¿Qué contienen?

```
debug/
├── airbnb_Aizeder_Eco_Container_20251106_143052.html  ← HTML capturado
├── airbnb_Aizeder_Eco_Container_20251106_143052.png   ← Screenshot
├── booking_Casa_del_Bosque_20251107_150330.html
└── booking_Casa_del_Bosque_20251107_150330.png
```

**Propósito:**
- Ver exactamente qué HTML recibió el scraper
- Debuggear selectores CSS cuando fallan
- Verificar si la página cargó correctamente
- **NO se usan para extraer datos posteriormente**

---

## ❌ Lo que NO Ocurre (Malentendidos Comunes)

### ❌ Mito 1: "Los datos se extraen de los HTML guardados"

**Falso.** Los datos se extraen **en tiempo real** del HTML en memoria mientras el navegador está abierto. Los archivos HTML son solo copias de respaldo.

### ❌ Mito 2: "Si se reemplaza el HTML debug, se pierden datos"

**Falso.** Los datos ya están guardados en `price_history.csv`. Reemplazar o borrar archivos debug **no afecta la base de datos**.

### ❌ Mito 3: "Necesito los archivos debug para que funcione el sistema"

**Falso.** El sistema funciona perfectamente sin archivos debug. De hecho, están **desactivados por defecto** en la app (`debug_first=False`).

---

## ✅ Solución al Problema de Nombres Duplicados

### Problema Original

**Antes de la corrección:**
```python
# Ambas propiedades generaban el mismo nombre de archivo
screenshot_path = f'debug_airbnb_20251106.png'
html_path = f'debug_airbnb_20251106.html'
```

**Resultado:**
```
Scraping Propiedad A (06/11) → debug_airbnb_20251106.html
Scraping Propiedad B (06/11) → debug_airbnb_20251106.html  ← SOBRESCRIBE!
```

### Solución Implementada

**Ahora con nombres únicos:**
```python
# Nombre de archivo único: plataforma + propiedad + fecha + timestamp
timestamp = datetime.now().strftime("%H%M%S")
safe_property_name = re.sub(r'[^\w\s-]', '', property_name).strip().replace(' ', '_')[:30]

filename = f'{platform}_{safe_property_name}_{checkin_date.strftime("%Y%m%d")}_{timestamp}.html'
```

**Resultado:**
```
Scraping Aizeder (06/11 14:30) → airbnb_Aizeder_Eco_Container_20251106_143052.html
Scraping Casa Bosque (06/11 14:30) → airbnb_Casa_Bosque_20251106_143055.html
Scraping Aizeder (07/11 10:00) → airbnb_Aizeder_Eco_Container_20251107_100012.html
```

**Ventajas:**
- ✅ Nunca se pisan archivos
- ✅ Fácil identificar qué propiedad
- ✅ Ordenados cronológicamente
- ✅ Timestamp único previene colisiones

---

## 📁 Organización de Archivos

### Estructura Completa

```
price-monitor/
│
├── data/                              ← BASE DE DATOS PRINCIPAL
│   ├── price_history.csv              ← ★ Todos los datos históricos
│   └── scrape_runs.json               ← Log anti-duplicado 48h
│
├── debug/                             ← ARCHIVOS DE TROUBLESHOOTING (opcionales)
│   ├── airbnb_Aizeder_Eco_Container_20251106_143052.html
│   ├── airbnb_Aizeder_Eco_Container_20251106_143052.png
│   ├── airbnb_Casa_del_Bosque_20251107_100012.html
│   ├── airbnb_Casa_del_Bosque_20251107_100012.png
│   ├── booking_Aizeder_Eco_Container_20251106_143230.html
│   └── booking_Aizeder_Eco_Container_20251106_143230.png
│
├── config/
│   └── competitors.json               ← Configuración de propiedades
│
└── src/
    ├── airbnb_scraper.py
    ├── booking_scraper.py
    ├── data_manager.py                ← Gestiona CSV y logs
    └── visualizer.py
```

---

## 🔄 Ciclo de Vida de los Datos

### Datos en `price_history.csv`

**Permanentes y acumulativos:**

```
Scraping 1 (Nov 6) → 20 registros → CSV con 20 filas
Scraping 2 (Nov 8) → 15 registros → CSV con 35 filas  ← Se agregan
Scraping 3 (Nov 10) → 18 registros → CSV con 53 filas ← Se agregan
```

**Nunca se sobrescriben, siempre se agregan.**

### Archivos Debug

**Temporales y opcionales:**

```
Scraping 1 → debug_A.html (se guarda)
Scraping 2 → debug_B.html (se guarda, diferente nombre)
Scraping 3 → debug_C.html (se guarda, diferente nombre)

Puedes borrar todos los archivos debug sin afectar los datos.
```

---

## 🎛️ Control de Archivos Debug desde la Interfaz

### Estado Actual (Desactivado)

En `app.py`:
```python
airbnb_results = airbnb.scrape_date_range(
    ...,
    debug_first=False  # ← No genera archivos debug
)

booking_results = booking.scrape_date_range(
    ...,
    debug_first=False  # ← No genera archivos debug
)
```

### Si Quieres Activar Debug

**Opción 1: Cambiar en app.py (permanente)**
```python
debug_first=True  # Guarda HTML/PNG del primer día scrapeado
```

**Opción 2: Agregar toggle en interfaz (futuro)**
```python
# En render_scraping_interface():
enable_debug = st.checkbox("🐛 Guardar archivos debug", value=False)

# Luego pasar:
debug_first=enable_debug
```

---

## 🧹 Gestión de Archivos Debug

### Borrar Archivos Antiguos

**Manualmente:**
```bash
cd /workspaces/price-monitor/debug
rm *.html *.png
```

**Script automático** (futuro):
```python
# Borrar archivos debug > 7 días
import os
from datetime import datetime, timedelta

debug_dir = 'debug'
cutoff = datetime.now() - timedelta(days=7)

for file in os.listdir(debug_dir):
    filepath = os.path.join(debug_dir, file)
    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
    if file_time < cutoff:
        os.remove(filepath)
        print(f"Eliminado: {file}")
```

---

## 📊 Comparación: CSV vs Debug

| Característica | price_history.csv | Archivos Debug |
|----------------|-------------------|----------------|
| **Propósito** | Base de datos principal | Troubleshooting |
| **Contenido** | Precios extraídos | HTML/PNG capturados |
| **Generación** | Siempre | Solo cuando `debug=True` o error |
| **Acumulación** | Se agregan filas | Archivos independientes |
| **Necesario** | ✅ Sí | ❌ No |
| **Usado por app** | ✅ Sí (visualizaciones) | ❌ No |
| **Tamaño** | Pequeño (CSV) | Grande (HTML/PNG) |
| **Backup** | Recomendado | Opcional |

---

## 🎯 Flujo Detallado Paso a Paso

### Ejemplo Real: Scrapear "Aizeder Eco Container"

**Paso 1: Usuario configura**
```
Propiedad: Aizeder Eco Container
Fechas: 6/11 - 13/11 (7 días)
Noches: 2
Huéspedes: 2
Plataformas: Airbnb + Booking
```

**Paso 2: App verifica anti-duplicado**
```python
is_recent = dm.is_recent_same_run(...)  # ¿Ya se scrapeó en 48h?
if is_recent and not force_run:
    return  # Bloqueado
```

**Paso 3: Scrapear Airbnb (7 días)**
```
Para cada día (6/11, 7/11, 8/11, ..., 12/11):
  1. Construir URL con fechas
  2. Abrir navegador Playwright
  3. Navegar a Airbnb
  4. Esperar carga
  5. Buscar precio en selectores CSS
  6. Extraer precio (ej: $150)
  7. Cerrar navegador
  8. Agregar resultado a lista:
     {platform: 'Airbnb', checkin: '2025-11-06', price_usd: 150, ...}
  
  (Si debug=True Y es el primer día):
     → Guardar airbnb_Aizeder_Eco_Container_20251106_143052.html
     → Guardar airbnb_Aizeder_Eco_Container_20251106_143052.png
```

**Paso 4: Scrapear Booking (7 días)**
```
(Mismo proceso para Booking)
Resultado: 7 registros más
```

**Paso 5: Guardar en CSV**
```python
dm.save_results(results, property_name='Aizeder Eco Container')

# Se agregan 14 filas a price_history.csv (7 Airbnb + 7 Booking)
```

**Paso 6: Registrar ejecución**
```python
dm.log_scrape_run(...)  # Para anti-duplicado 48h
```

**Resultado final:**
```
✅ data/price_history.csv → +14 filas nuevas
✅ data/scrape_runs.json → +1 registro de ejecución
❓ debug/ → 0-2 archivos (solo si debug=True o error)
```

---

## 💡 Mejores Prácticas

### ✅ Hacer

1. **Mantener `price_history.csv` siempre**
   - Es tu base de datos principal
   - Hacer backups periódicos

2. **Borrar archivos debug antiguos**
   - Ocupan espacio innecesariamente
   - No afectan funcionalidad

3. **Activar debug solo cuando hay problemas**
   - Útil para debugging
   - No necesario en producción

4. **Verificar el CSV después de scrapear**
   - Ver que se agregaron las filas correctas
   - Detectar errores temprano

### ❌ Evitar

1. **No borrar `price_history.csv`**
   - Perderías todos los datos históricos
   - Hacer backup antes

2. **No depender de archivos debug**
   - No son parte del flujo normal
   - Pueden no existir

3. **No asumir que debug → datos**
   - Los datos vienen del scraping en vivo
   - Debug es solo copia de respaldo

---

## 🔧 Configuración de Debug (Avanzado)

### Cambiar Directorio de Debug

En `airbnb_scraper.py` y `booking_scraper.py`:
```python
class AirbnbScraper:
    def __init__(self):
        self.debug_dir = 'debug'  # ← Cambiar aquí
```

### Organizar por Fechas

```python
# Crear subcarpetas por mes
import os
from datetime import datetime

month_dir = datetime.now().strftime("%Y_%m")
self.debug_dir = os.path.join('debug', month_dir)
os.makedirs(self.debug_dir, exist_ok=True)

# Resultado:
# debug/
#   2025_11/
#     airbnb_...
#   2025_12/
#     airbnb_...
```

---

## ✅ Resumen Final

| Pregunta | Respuesta |
|----------|-----------|
| ¿Los datos vienen de HTML debug? | ❌ NO. Se extraen en tiempo real |
| ¿Se reemplazan archivos debug? | ❌ NO. Ahora tienen nombres únicos |
| ¿Necesito archivos debug? | ❌ NO. Son opcionales |
| ¿Dónde está la base de datos? | ✅ `data/price_history.csv` |
| ¿Se pierden datos al borrar debug? | ❌ NO. CSV está intacto |
| ¿Los archivos debug se pisan? | ❌ NO. Timestamp único |

---

**Fecha:** 6 de noviembre de 2025  
**Versión:** 2.1  
**Sistema:** Price Monitor
