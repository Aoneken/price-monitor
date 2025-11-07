# PLAN DE REFACTORIZACIÓN - Metodología de Extracción Robusta
**Fecha:** 7 de noviembre, 2025  
**Objetivo:** Diseñar e implementar un método de extracción confiable y mantenible

---

## 🎯 FASE 1: INVESTIGACIÓN Y RECOLECCIÓN DE DATOS (TU AYUDA)

### **Necesito que hagas lo siguiente:**

#### 1️⃣ **Inspección Manual en Navegador Real** (15 minutos)

Abre en tu navegador (Chrome/Firefox) una de las URLs de Airbnb configuradas con fechas específicas:

**URL de ejemplo:**
```
https://www.airbnb.es/rooms/[ID]?checkin=2025-12-15&checkout=2025-12-18
```

**Instrucciones detalladas:**

> **📝 OBSERVACIONES DEL USUARIO:**
> 1. La URL con parámetros se transforma automáticamente y agrega `source_impression_id`
> 2. Aparecen modales que ocultan el contenido:
>    - Modal de "Traducción activada"
>    - Modal de cookies "Ayúdanos a mejorar tu experiencia"
> 3. En el segundo ingreso estos modales ya no aparecen (cookies aceptadas)

##### A) **Verificar Disponibilidad Visual**
- [ ] ¿Ves un precio visible en la página? (ej: "$150 por noche")
- [ ] ¿Qué mensaje aparece si NO está disponible?


> **📝 HALLAZGO CRÍTICO DEL USUARIO:**
> ❌ **NO HAY PRECIO VISIBLE** en la página
> 
> **Mensaje mostrado:**
> ```
> "Añade las fechas para consultar los precios
> Llegada - Añade la fecha
> Salida - Añade la fecha
> Huéspedes - 1 viajero"
> ```
> 
> **Interpretación:** La URL NO está respetando los parámetros `checkin` y `checkout`.
> Airbnb está ignorando las fechas en la URL y mostrando la página sin fechas seleccionadas.

##### B) **Inspeccionar Código Fuente** (F12 → Elements)
1. **Botón derecho sobre el precio → Inspeccionar**
2. Copiar el HTML completo del elemento precio:
   ```html
   <!-- Ejemplo de lo que necesito ver -->
   <span class="a8jt5op" dir="ltr">
     <span class="_tyxjp1">$150</span>
   </span>
   ```
3. **Árbol de padres**: Copiar también los 3-4 elementos padres
4. Buscar atributos únicos:
   - `data-testid="..."`
   - `aria-label="..."`
   - IDs o clases específicas

##### C) **Inspeccionar Network Tab** (F12 → Network)
1. **Recargar la página** (Ctrl+R)
2. Buscar llamadas a APIs:
   - Filtrar por "XHR" o "Fetch"
   - Buscar endpoints con "price", "booking", "availability"
3. **CRUCIAL**: Si encuentras una llamada API con precios en JSON:
   - Click derecho → "Copy as cURL"
   - Pegar el comando completo

##### D) **Inspeccionar Console/Sources** (F12 → Console)
1. Escribir en consola:
   ```javascript
   // Buscar datos en window
   Object.keys(window).filter(k => k.includes('data') || k.includes('state'))
   
   // Ver si hay datos de Next.js
   window.__NEXT_DATA__
   
   // Ver si hay Apollo State
   document.querySelector('[data-state]')?.getAttribute('data-state')
   ```
2. Copiar el output

---

#### 2️⃣ **Información Específica que Necesito**

Por favor, crea un documento/mensaje con:

```markdown
## Inspección de Airbnb - [Fecha]

### URL Probada:
[pegar URL completa]

### Disponibilidad:
- [ ] Sí, hay precio visible: $_____ por noche
- [ ] No, mensaje de no disponible: "___________"

### HTML del Precio:
```html
[pegar elemento HTML completo]
```

### Selectores Posibles:
- Clase principal: _______________
- data-testid: _______________
- aria-label: _______________

### Network API (si aplica):
```bash
[pegar cURL completo]
```
O describir:
- Endpoint: _______________
- Método: GET/POST
- Response incluye precio: Sí/No

### Datos en Window/Console:
```javascript
[pegar output de comandos console]
```

### Screenshots:
[adjuntar o describir ubicación]
```

---

## 🛠️ FASE 2: DISEÑO DE NUEVA METODOLOGÍA (YO)

Basado en tu inspección, diseñaré:

### **Estrategia por Prioridad:**

1. **API First** (si existe)
   - Interceptar llamadas HTTP reales
   - Parsear JSON directamente
   - **Ventaja**: 100% confiable, no depende de DOM

2. **JSON Embebido** (window.__NEXT_DATA__, etc.)
   - Extraer desde estado de React/Next.js
   - **Ventaja**: Muy confiable, más rápido que esperar DOM

3. **DOM con Selectores Múltiples**
   - Usar tus selectores + fallbacks
   - **Ventaja**: Funciona si API no es accesible

4. **Regex Inteligente**
   - Última opción sobre texto plano
   - **Ventaja**: Siempre funciona como último recurso

### **Arquitectura Nueva:**

```python
class ExtractorStrategy(ABC):
    @abstractmethod
    def extract(self, page: Page) -> Optional[float]:
        pass

class APIExtractor(ExtractorStrategy):
    """Intercepta llamadas HTTP"""
    
class WindowDataExtractor(ExtractorStrategy):
    """Extrae desde window.__NEXT_DATA__"""
    
class DOMExtractor(ExtractorStrategy):
    """Selectores CSS con tus datos"""
    
class RegexExtractor(ExtractorStrategy):
    """Fallback final"""

class RobustPriceExtractor:
    def __init__(self):
        self.strategies = [
            APIExtractor(),
            WindowDataExtractor(),
            DOMExtractor(),
            RegexExtractor()
        ]
    
    def extract(self, page: Page) -> Optional[float]:
        for strategy in self.strategies:
            try:
                price = strategy.extract(page)
                if price:
                    return price
            except Exception as e:
                logger.debug(f"Strategy {strategy} failed: {e}")
        return None
```

---

## 🚀 FASE 3: IMPLEMENTACIÓN (COLABORATIVA)

1. **Yo implemento** la nueva arquitectura
2. **Tú pruebas** con URLs reales
3. **Iteramos** basados en resultados

### ✅ Avance al 7/11/2025
- URL builder actualizado con formato estable + fallback y moneda forzada a USD.
- Robots `airbnb_robot` y `airbnb_robot_v2` integran `RobustPriceExtractor` (API → Window → DOM → Regex).
- Se registra cada intento y se guarda debug solo cuando el extractor no encuentra precio.
- Pendiente: validar en entorno real y ajustar estrategias específicas según nuevos hallazgos.

---

## ⏱️ TIEMPO ESTIMADO

- **Tu parte**: 15-20 minutos de inspección
- **Mi parte**: 1-2 horas de implementación
- **Testing conjunto**: 30 minutos

---

## 📝 FORMATO DE RESPUESTA RÁPIDA

Si prefieres formato más rápido, puedes responder:

**Formato Compacto:**
```
URL: [url]
PRECIO VISIBLE: Sí/No - $XXX
SELECTOR: span.clase123
API: Sí/No - [endpoint si hay]
WINDOW DATA: Sí/No - [describir]
```

---

## 🎯 SIGUIENTE PASO INMEDIATO

**¿Puedes hacer la inspección ahora?** 

Si sí:
- Te recomiendo usar una URL de **diciembre 2025** en adelante (más probabilidad de tener disponibilidad)
- Enfócate primero en **Network tab** (APIs son gold)

Si no puedes ahora:
- Dime cuándo podrías y preparo todo para maximizar eficiencia

**¿Qué opción prefieres?**
A) Hago inspección completa ahora (15 min)
B) Hago inspección rápida ahora (5 min - solo lo esencial)
C) La hago más tarde, avisa para preparar scripts
D) No tengo acceso a navegador, busquemos alternativa

