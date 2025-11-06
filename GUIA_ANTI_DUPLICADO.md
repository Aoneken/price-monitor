# 📖 Guía de Uso: Sistema Anti-Duplicado 48h

## 🎯 ¿Qué hace este sistema?

El sistema **previene automáticamente** que ejecutes el mismo scraping dos veces en un periodo de 48 horas. Esto te ayuda a:

- ✅ Ahorrar recursos computacionales
- ✅ Evitar posibles bloqueos de las plataformas (anti-ban)
- ✅ Mantener tus datos organizados sin duplicados
- ✅ Tener un registro de todas tus ejecuciones

---

## 📱 Cómo Usar en la Interfaz

### Paso 1: Configura tu Scraping Normalmente

1. Ve a la pestaña **"🔍 Nuevo Scraping"**
2. Selecciona una propiedad
3. Configura las fechas, noches y huéspedes
4. Selecciona las plataformas (Airbnb, Booking, o ambas)

### Paso 2: Inicia el Scraping

- Si **NO** existe una ejecución reciente → ✅ El scraping procede normalmente
- Si **SÍ** existe una ejecución reciente → ⚠️ Verás un mensaje de advertencia

### Paso 3: Si se Detecta Duplicado

Aparecerá un mensaje como este:

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

**Tienes dos opciones:**

1. **Esperar 48 horas** y volver a intentar
2. **Marcar el checkbox "🔄 Forzar ejecución"** y hacer clic de nuevo en "Iniciar Scraping"

---

## 🔄 Usando "Forzar Ejecución"

### ¿Cuándo usarlo?

✅ **Úsalo cuando:**
- Necesitas datos actualizados urgentemente
- Sabes que los precios han cambiado significativamente
- Estás haciendo pruebas o debugging
- Hubo un error en la ejecución anterior

❌ **NO lo uses cuando:**
- Solo quieres "refrescar" datos sin razón específica
- Ya tienes datos recientes (< 48h)
- Estás ejecutando el mismo scraping repetidamente

### Cómo activarlo:

1. Después de ver el mensaje de advertencia
2. Marca el checkbox **"🔄 Forzar ejecución"**
3. Haz clic de nuevo en **"🚀 Iniciar Scraping"**
4. El scraping se ejecutará ignorando el control anti-duplicado

---

## 🧮 ¿Qué se Considera "Duplicado"?

El sistema compara **TODOS** estos parámetros:

| Parámetro | Descripción |
|-----------|-------------|
| Propiedad | Nombre exacto de la propiedad |
| Fecha inicio | Día de check-in |
| Fecha fin | Día de check-out |
| Noches | Duración de la estadía |
| Huéspedes | Número de personas |
| Plataformas | Airbnb, Booking, o ambas |
| Tiempo | Última ejecución < 48 horas |

Si **CUALQUIERA** de estos es diferente, el scraping procederá sin restricciones.

---

## 📊 Ejemplos Prácticos

### ✅ Ejemplo 1: Configuración Idéntica (BLOQUEADO)

**Ejecución 1 (hoy a las 10:00)**
- Propiedad: Aizeder Eco Container
- Fechas: 6/11 - 13/11
- Noches: 2
- Huéspedes: 2
- Plataformas: Airbnb + Booking

**Ejecución 2 (hoy a las 14:00)**
- Propiedad: Aizeder Eco Container
- Fechas: 6/11 - 13/11
- Noches: 2
- Huéspedes: 2
- Plataformas: Airbnb + Booking

**Resultado:** ⚠️ **BLOQUEADO** (todo es idéntico y pasaron solo 4 horas)

---

### ✅ Ejemplo 2: Fechas Diferentes (PERMITIDO)

**Ejecución 1**
- Fechas: 6/11 - 13/11

**Ejecución 2**
- Fechas: **7/11 - 14/11** ← Diferente

**Resultado:** ✅ **PERMITIDO** (las fechas son diferentes)

---

### ✅ Ejemplo 3: Más Huéspedes (PERMITIDO)

**Ejecución 1**
- Huéspedes: 2

**Ejecución 2**
- Huéspedes: **4** ← Diferente

**Resultado:** ✅ **PERMITIDO** (el número de huéspedes cambió)

---

### ✅ Ejemplo 4: Solo una Plataforma (PERMITIDO)

**Ejecución 1**
- Plataformas: Airbnb + Booking

**Ejecución 2**
- Plataformas: **Solo Airbnb** ← Diferente

**Resultado:** ✅ **PERMITIDO** (las plataformas seleccionadas son diferentes)

---

### ✅ Ejemplo 5: Después de 48h (PERMITIDO)

**Ejecución 1**
- Timestamp: Lunes 6/11 a las 10:00

**Ejecución 2**
- Timestamp: Miércoles 8/11 a las 11:00

**Resultado:** ✅ **PERMITIDO** (han pasado más de 48 horas)

---

## 🔧 Verificar el Historial

Aunque no hay una interfaz visual todavía, puedes ver todas las ejecuciones registradas en:

```
data/scrape_runs.json
```

Cada registro contiene:
```json
{
  "property_name": "Nombre de la Propiedad",
  "start_date": "2025-11-06",
  "end_date": "2025-11-13",
  "nights": 2,
  "guests": 2,
  "platforms": ["airbnb", "booking"],
  "ts": "2025-11-06T16:23:51"
}
```

---

## 💡 Tips y Buenas Prácticas

### 🎯 Planifica tus Scrapings
- Define un calendario de actualización (ej: cada 3 días)
- No necesitas scrapear todos los días a menos que los precios sean muy volátiles

### 📊 Usa Configuraciones Diferentes
- Si necesitas datos más frecuentes, varía algún parámetro (ej: rango de fechas)
- Esto te permitirá obtener una visión más completa sin duplicar exactamente

### 🔄 Reserva "Forzar Ejecución" para Casos Especiales
- No lo uses por defecto
- Solo cuando realmente necesites override del control

### 📅 Conoce la Ventana de 48h
- Si scrapeaste hoy a las 14:00, podrás volver a scrapear la misma config pasado mañana a las 14:01
- El control es exacto al segundo

---

## ❓ Preguntas Frecuentes

### ¿Puedo cambiar la ventana de 48 horas?

Sí, pero requiere modificar el código en `app.py`. Busca:
```python
window_hours=48  # Cambia este valor
```

### ¿Qué pasa si borro el archivo scrape_runs.json?

El sistema empezará de cero y no recordará ejecuciones anteriores. Todas las nuevas ejecuciones se permitirán.

### ¿El sistema consume mucho espacio?

No. Cada registro ocupa ~200 bytes. Incluso con 1000 ejecuciones, el archivo pesaría menos de 200KB.

### ¿Se sincroniza con otros usuarios?

No. El archivo `scrape_runs.json` es local a tu instalación. Cada usuario tiene su propio historial.

### ¿Afecta a los datos ya guardados?

No. Este sistema solo controla **cuándo** se ejecutan scrapings. Los datos en `price_history.csv` no se ven afectados.

---

## 🎓 Resumen Visual

```
┌─────────────────────────────────────┐
│ Usuario configura scraping          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Sistema verifica si existe          │
│ ejecución idéntica < 48h            │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
   [SÍ existe]     [NO existe]
       │                │
       │                ▼
       │          ✅ Scraping
       │             procede
       │                │
       ▼                ▼
   ⚠️ Warning      💾 Guarda datos
   mostrado            │
       │                ▼
       │          📝 Registra
       │             ejecución
       │                │
       ▼                │
   ┌─────────┐         │
   │ ¿Forzar?│         │
   └────┬────┘         │
        │              │
    ┌───┴───┐          │
    │       │          │
   NO      SÍ          │
    │       │          │
    ▼       └──────────┘
 ❌ Fin           ✅ Fin
 (bloqueado)    (exitoso)
```

---

**Fecha:** 6 de noviembre de 2025  
**Sistema:** Price Monitor v2.1  
**Característica:** Control Anti-Duplicado 48h
