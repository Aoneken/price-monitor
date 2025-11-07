# 🔴 PROBLEMA CRÍTICO IDENTIFICADO - Airbnb Ignora Parámetros de URL

**Fecha:** 7 de noviembre, 2025  
**Descubrimiento:** Inspección manual del usuario

---

## ❌ EL VERDADERO PROBLEMA

**Airbnb NO está respetando los parámetros de fecha en la URL.**

### Evidencia:

**URL enviada:**
```
https://www.airbnb.es/rooms/1413234233737891700?checkin=2025-12-15&checkout=2025-12-18
```

**Resultado en la página:**
```
"Añade las fechas para consultar los precios
Llegada - Añade la fecha
Salida - Añade la fecha
Huéspedes - 1 viajero"
```

**Conclusión inicial:** La página cargaba VACÍA, sin fechas seleccionadas, por lo tanto **nunca había precio visible**.

**Estado actual (07/11/2025):**
- ✅ Descubrimos el formato correcto de URL (`check_in`, `check_out`, `currency=USD`).
- ✅ Agregamos un `source_impression_id` genérico y un fallback con `children=0&infants=0`.
- ✅ Las URLs probadas manualmente muestran precios en USD sin intervención adicional.
- ✅ El `URLBuilder.airbnb_url_variants` genera automáticamente ambos formatos.
- ✅ El robot usa un extractor robusto (API/Window/DOM/Regex) y prueba ambas URLs antes de fallar.

---

## 🔍 POR QUÉ NUESTRO SCRAPER FALLA

Ahora todo tiene sentido:

1. ✅ El navegador SÍ carga la página correctamente
2. ✅ El contenido SÍ se renderiza (React/Next.js funciona)
3. ❌ **Pero las fechas NO están seleccionadas**
4. ❌ Por lo tanto, **Airbnb NO muestra precio** (porque no hay búsqueda activa)
5. ❌ Nuestros selectores fallan porque **el precio literalmente no existe en el DOM**

---

## 💡 SOLUCIONES POSIBLES

### **OPCIÓN 1: Interactuar con el Calendario** ⭐ (Recomendada)

En lugar de confiar en parámetros URL, **simular clicks de usuario**:

```python
# Pseudo-código
page.goto(url_base)  # Sin parámetros de fecha
page.click('[data-testid="checkin-button"]')  # Abrir calendario
page.click(f'[data-date="{checkin}"]')  # Seleccionar fecha entrada
page.click(f'[data-date="{checkout}"]')  # Seleccionar fecha salida
page.wait_for_selector('[data-testid="price-display"]')  # Esperar precio
precio = extraer_precio(page)
```

**Ventajas:**
- ✅ Simula comportamiento humano real
- ✅ Airbnb responderá con precio verdadero
- ✅ Menos detección de bot

**Desventajas:**
- ⚠️ Más lento (requiere interacción)
- ⚠️ Más complejo (manejo de calendario)

---

### **OPCIÓN 2: Interceptar API de Búsqueda** ⭐⭐ (Más Robusta)

Cuando el usuario hace click en fechas, Airbnb llama a una API. Podemos:

1. Analizar la llamada API que hace Airbnb
2. Replicarla directamente con `requests` o `httpx`
3. Parsear el JSON de respuesta

**Ventajas:**
- ✅ MUY rápido (sin navegador)
- ✅ 100% confiable (datos directos de API)
- ✅ No hay detección de bot

**Desventajas:**
- ⚠️ Requiere reverse engineering de la API
- ⚠️ Puede requerir headers/cookies específicos
- ⚠️ Si Airbnb cambia la API, hay que adaptar

---

### **OPCIÓN 3: Formato de URL Correcto** ⚠️ (Investigar)

Posiblemente Airbnb cambió el formato de parámetros URL. Necesitamos:

1. Hacer una búsqueda manual en Airbnb
2. Copiar la URL resultante
3. Analizar el formato exacto de parámetros

**Ejemplo posible:**
```
# Formato viejo (no funciona)
?checkin=2025-12-15&checkout=2025-12-18

# Formato nuevo (hipotético)
?check_in=2025-12-15&check_out=2025-12-18
# O con timestamps
?checkin_timestamp=1734220800&checkout_timestamp=1734480000
```

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### **Te pido que hagas esto AHORA** (5 minutos):

#### 1. **Búsqueda Manual Correcta:**

1. Ve a https://www.airbnb.es
2. Usa el buscador principal:
   - Destino: "El Chaltén, Argentina"
   - Fechas: 15 dic - 18 dic 2025
   - Huéspedes: 2
3. Click en "Buscar"
4. **Selecciona UNO de los resultados** (cualquier alojamiento)
5. **COPIA LA URL COMPLETA** de la barra del navegador

**La URL debe verse algo así:**
```
https://www.airbnb.es/rooms/12345?adults=2&check_in=2025-12-15&check_out=2025-12-18&...
```

#### 2. **Verificar Network:**

Con DevTools abierto (F12 → Network):
1. Haz la búsqueda desde cero
2. Busca llamadas con:
   - `StaysPdp` o `PdpAvailabilityCalendar`
   - Cualquier endpoint que incluya "price" o "availability"
3. **Si encuentras algo, copia como cURL**

---

## 🔧 MIENTRAS TANTO (YO TRABAJO EN):

### **Implementación de Solución con Interacción:**

Voy a preparar un robot que:
1. Carga la página base
2. Interactúa con el calendario
3. Espera a que aparezca el precio
4. Extrae el precio

Archivo: `scrapers/robots/airbnb_robot_interactive.py`

---

## 📊 TIEMPO ESTIMADO

- **Tu investigación**: 5-10 minutos
- **Mi implementación**: 45-60 minutos
- **Testing conjunto**: 15 minutos

**Total: ~1.5 horas para solución completa**

---

## 💬 RESPONDE CON:

```markdown
### Búsqueda Manual Correcta

**URL completa del alojamiento con fechas:**
[pegar]

**¿El precio aparece ahora?**
- [ ] Sí: $_____ por noche
- [ ] No: [describir qué ves]

**Network Tab:**
- [ ] Encontré API: [nombre del endpoint]
      cURL: [pegar si es posible]
- [ ] No encontré nada relevante

**Formato de parámetros observado:**
check_in=... o checkin=... o timestamp=...
```

---

## 🚨 NOTA IMPORTANTE

Este descubrimiento explica por qué **TODOS** los scrapings previos fallaron:

- No es problema de selectores ❌
- No es problema de timing ❌  
- No es problema de stealth ❌
- **ES PROBLEMA DE PARÁMETROS URL** ✅

Una vez que tengamos el formato correcto de URL (o implementemos interacción), el sistema funcionará.

---

¿Puedes hacer esa búsqueda manual ahora? Es crítico para avanzar. 🚀
