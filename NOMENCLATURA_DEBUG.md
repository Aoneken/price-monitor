# 🎨 Diagrama Visual: Nomenclatura de Archivos Debug

## 📝 Formato de Nombres (NUEVO)

```
{plataforma}_{propiedad_normalizada}_{fecha}_{timestamp}.{ext}
    │              │                    │         │        │
    │              │                    │         │        └─ Extensión (.html o .png)
    │              │                    │         └─ Hora exacta (HHMMSS) para unicidad
    │              │                    └─ Fecha de check-in (YYYYMMDD)
    │              └─ Nombre de propiedad sin caracteres especiales (max 30 chars)
    └─ Plataforma (airbnb o booking)
```

---

## 🔍 Ejemplos de Nombres Generados

### Ejemplo 1: Aizeder Eco Container House

**Scraping 1:**
```
Propiedad: "Aizeder Eco Container House"
Fecha check-in: 2025-11-06
Hora: 14:30:52
Plataforma: Airbnb

Nombres generados:
├─ airbnb_Aizeder_Eco_Container_House_20251106_143052.html
└─ airbnb_Aizeder_Eco_Container_House_20251106_143052.png
```

**Scraping 2 (misma propiedad, 5 minutos después):**
```
Propiedad: "Aizeder Eco Container House"
Fecha check-in: 2025-11-06
Hora: 14:35:18
Plataforma: Airbnb

Nombres generados:
├─ airbnb_Aizeder_Eco_Container_House_20251106_143518.html  ← DIFERENTE timestamp
└─ airbnb_Aizeder_Eco_Container_House_20251106_143518.png
```

**✅ Resultado:** Ambos archivos coexisten sin conflictos

---

### Ejemplo 2: Casa del Bosque

```
Propiedad: "Casa del Bosque"
Fecha check-in: 2025-11-07
Hora: 10:00:12
Plataforma: Booking

Nombres generados:
├─ booking_Casa_del_Bosque_20251107_100012.html
└─ booking_Casa_del_Bosque_20251107_100012.png
```

---

### Ejemplo 3: Nombre Largo con Caracteres Especiales

```
Propiedad: "¡Súper Casa! @Beautiful Retreat & More..."
         ↓ (normalización)
         "Super_Casa_Beautiful_Retreat"  ← 30 chars máximo

Nombres generados:
├─ airbnb_Super_Casa_Beautiful_Retreat_20251108_153045.html
└─ airbnb_Super_Casa_Beautiful_Retreat_20251108_153045.png
```

**Normalización aplicada:**
- Elimina: `¡ ! @ & . ...`
- Reemplaza espacios con `_`
- Trunca a 30 caracteres
- Solo caracteres alfanuméricos, guiones y guiones bajos

---

## 📁 Vista de Carpeta `debug/`

### Antes (Problema: Nombres se pisaban)

```
debug/
├── debug_airbnb_20251106.html        ← Propiedad A
├── debug_airbnb_20251106.png         ← Propiedad A
├── debug_airbnb_20251106.html        ← Propiedad B (SOBRESCRIBE A)
├── debug_airbnb_20251106.png         ← Propiedad B (SOBRESCRIBE A)
├── debug_booking_20251106.html
└── debug_booking_20251106.png

Total: 6 archivos (pero datos de A se perdieron!)
```

### Ahora (Solución: Nombres únicos)

```
debug/
├── airbnb_Aizeder_Eco_Container_House_20251106_143052.html
├── airbnb_Aizeder_Eco_Container_House_20251106_143052.png
├── airbnb_Casa_del_Bosque_20251106_143518.html
├── airbnb_Casa_del_Bosque_20251106_143518.png
├── airbnb_Aizeder_Eco_Container_House_20251107_100012.html
├── airbnb_Aizeder_Eco_Container_House_20251107_100012.png
├── booking_Aizeder_Eco_Container_House_20251106_143230.html
├── booking_Aizeder_Eco_Container_House_20251106_143230.png
├── booking_Casa_del_Bosque_20251106_143645.html
├── booking_Casa_del_Bosque_20251106_143645.png
├── booking_Aizeder_Eco_Container_House_20251107_100145.html
└── booking_Aizeder_Eco_Container_House_20251107_100145.png

Total: 12 archivos (todos únicos y organizados!)
```

**Ventajas:**
- ✅ Fácil buscar por propiedad: `ls debug/airbnb_Aizeder*`
- ✅ Fácil buscar por fecha: `ls debug/*_20251106_*`
- ✅ Fácil buscar por plataforma: `ls debug/booking_*`
- ✅ Ordenamiento alfabético natural
- ✅ Nunca hay colisiones

---

## 🔍 Búsquedas Útiles

### Por Propiedad

```bash
# Todos los archivos de Aizeder
ls debug/*Aizeder*

# Solo HTML de Aizeder
ls debug/*Aizeder*.html

# Solo Airbnb de Aizeder
ls debug/airbnb_Aizeder*
```

### Por Fecha

```bash
# Todo del 6 de noviembre
ls debug/*20251106*

# Solo screenshots del 6 de noviembre
ls debug/*20251106*.png
```

### Por Plataforma

```bash
# Todo de Airbnb
ls debug/airbnb_*

# Todo de Booking
ls debug/booking_*
```

### Por Hora (para debugging fino)

```bash
# Entre las 14:30 y 14:40
ls debug/*_143[0-9][0-9][0-9].*
```

---

## 🗂️ Organización Avanzada (Opcional)

### Opción 1: Subcarpetas por Propiedad

```python
# En scrapers:
safe_name = re.sub(r'[^\w\s-]', '', property_name).strip().replace(' ', '_')[:30]
property_dir = os.path.join(self.debug_dir, safe_name)
os.makedirs(property_dir, exist_ok=True)

# Resultado:
debug/
├── Aizeder_Eco_Container_House/
│   ├── airbnb_20251106_143052.html
│   ├── airbnb_20251106_143052.png
│   ├── booking_20251106_143230.html
│   └── booking_20251106_143230.png
└── Casa_del_Bosque/
    ├── airbnb_20251106_143518.html
    ├── airbnb_20251106_143518.png
    ├── booking_20251106_143645.html
    └── booking_20251106_143645.png
```

### Opción 2: Subcarpetas por Fecha

```python
# En scrapers:
date_dir = checkin_date.strftime("%Y_%m_%d")
dated_dir = os.path.join(self.debug_dir, date_dir)
os.makedirs(dated_dir, exist_ok=True)

# Resultado:
debug/
├── 2025_11_06/
│   ├── airbnb_Aizeder_143052.html
│   ├── airbnb_Casa_143518.html
│   └── booking_Aizeder_143230.html
└── 2025_11_07/
    ├── airbnb_Aizeder_100012.html
    └── booking_Casa_100145.html
```

### Opción 3: Jerarquía Completa (Año/Mes/Propiedad)

```
debug/
├── 2025/
│   ├── 11_Nov/
│   │   ├── Aizeder_Eco_Container_House/
│   │   │   ├── airbnb_06_143052.html
│   │   │   └── booking_06_143230.html
│   │   └── Casa_del_Bosque/
│   │       └── airbnb_06_143518.html
│   └── 12_Dec/
│       └── ...
└── 2024/
    └── ...
```

---

## 🧹 Scripts de Limpieza

### 1. Borrar por Antigüedad

```bash
# Borrar archivos debug > 7 días
find debug/ -type f -mtime +7 -delete

# Borrar archivos debug > 30 días
find debug/ -type f -mtime +30 -delete
```

### 2. Borrar por Propiedad

```bash
# Borrar todos los archivos de "Casa del Bosque"
rm debug/*Casa_del_Bosque*
```

### 3. Borrar por Fecha

```bash
# Borrar todo del mes de octubre
rm debug/*202510*
```

### 4. Mantener Solo Errores

```python
# Script Python para conservar solo archivos de scrapings con error
import os
import pandas as pd

# Cargar historial
df = pd.read_csv('data/price_history.csv')

# Encontrar scrapings exitosos (con precio)
successful = df[df['price_usd'].notna()]

# Construir lista de archivos a preservar
# (lógica basada en timestamps y nombres)

# Borrar el resto
```

---

## 📊 Estadísticas de Archivos

### Tamaños Típicos

| Tipo | Tamaño Promedio | Ejemplo |
|------|----------------|---------|
| HTML | 200-500 KB | 300 KB |
| PNG (screenshot) | 500-1500 KB | 800 KB |
| **Total por scraping** | ~1 MB | 1.1 MB |

### Proyección de Espacio

```
1 propiedad × 7 días × 2 plataformas = 14 scrapings
14 scrapings × 1 MB = ~14 MB por semana

Con 10 propiedades:
10 × 14 MB = 140 MB por semana
       ×4  = 560 MB por mes
      ×12  = 6.7 GB por año
```

**Recomendación:** Limpiar archivos debug cada 7-30 días para controlar espacio.

---

## 🎯 Resumen de Cambios

### Antes

```
debug_airbnb_20251106.html
debug_airbnb_20251106.png
```

**Problemas:**
- ❌ Múltiples propiedades pisan archivos
- ❌ No se sabe qué propiedad es
- ❌ Difícil organizar

### Ahora

```
airbnb_Aizeder_Eco_Container_House_20251106_143052.html
airbnb_Aizeder_Eco_Container_House_20251106_143052.png
```

**Ventajas:**
- ✅ Nombres únicos garantizados (timestamp)
- ✅ Identificación clara de propiedad
- ✅ Ordenamiento natural
- ✅ Búsquedas granulares
- ✅ Escalable

---

## 🔐 Seguridad y Privacidad

### Nombres de Archivo Seguros

La normalización elimina caracteres peligrosos:

```python
# Entrada:
"My <script>alert('xss')</script> Property"

# Salida (normalizada):
"My_scriptalertxssscript_Prope"  # Truncado a 30 chars
```

**Previene:**
- ❌ Inyección de comandos
- ❌ Path traversal (`../../../`)
- ❌ Caracteres no válidos en filesystems

---

**Implementado:** 6 de noviembre de 2025  
**Estado:** ✅ Producción  
**Testing:** Pendiente casos edge
