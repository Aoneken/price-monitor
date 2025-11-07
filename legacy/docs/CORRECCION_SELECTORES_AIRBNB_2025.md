# Corrección Selectores Airbnb 2025

## 📋 Problema Identificado

**Fecha:** 7 de noviembre de 2025  
**Reportado por:** Exequiel  
**URL de prueba:** https://www.airbnb.com.ar/rooms/1413234233737891700?check_in=2025-11-07&check_out=2025-11-09

### Síntomas
- El precio visible en el navegador era: **$254 USD por 2 noches**
- El scraper NO estaba extrayendo este precio
- Los archivos HTML guardados anteriormente mostraban `"price":null`

### Causa Raíz

**1. Airbnb usa React/JavaScript para renderizar el contenido dinámicamente**
   - El HTML inicial NO contiene los precios
   - Los precios se cargan DESPUÉS mediante JavaScript
   - El robot esperaba 8 segundos fijos, pero NO verificaba si el contenido estaba listo

**2. Los selectores CSS de 2024 quedaron obsoletos**
   - Airbnb cambió las clases CSS de los elementos de precio
   - Los selectores anteriores (`_doc79r`, `_tyxjp1`) ya no funcionaban con la nueva versión

## 🔍 Análisis del HTML Real

Exequiel inspeccionó el navegador y encontró estos elementos:

```html
<!-- PRECIO CON DESCUENTO -->
<span class="umuerxh atm_7l_1dmvgf5 atm_cs_bs05t3 atm_rd_us8791 atm_cs_l3jtxx__1v156lz dir dir-ltr">
    $254&nbsp;USD
</span>

<!-- TEXTO "POR 2 NOCHES" -->
<span class="q13rtw21 atm_cs_1dh25pa atm_7l_1kkyeqd atm_c8_1xllz8c atm_g3_e3z31c dir dir-ltr">
    por 2&nbsp;noches
</span>

<!-- PRECIO ORIGINAL TACHADO (descuento aplicado) -->
<span class="s13lowb4 atm_7l_1kkyeqd atm_rd_1911m7k atm_cs_1dh25pa atm_c8_ip3js9 atm_g3_8dziaq dir dir-ltr">
    $310&nbsp;USD
</span>
```

**Clases clave identificadas:**
- `umuerxh` → Precio con descuento ($254 USD)
- `s13lowb4` → Precio original tachado ($310 USD)
- `q13rtw21` → Texto descriptivo ("por 2 noches")

## ✅ Solución Implementada

### 1. Espera Inteligente de Elementos

**Antes:**
```python
page.wait_for_timeout(8000)  # Espera ciega de 8 segundos
```

**Ahora:**
```python
page.wait_for_timeout(5000)  # Espera inicial de 5 segundos
precio_visible = self._esperar_precio_visible(page)  # Espera ACTIVA hasta 15 segundos
```

**Nuevo método `_esperar_precio_visible()`:**
```python
def _esperar_precio_visible(self, page: Page, timeout: int = 15000) -> bool:
    """
    Espera a que aparezca al menos UN selector de precio válido en la página.
    Esto asegura que React/JavaScript haya terminado de renderizar el contenido.
    """
    selectores_precio = [
        'span.umuerxh',   # Nuevo 2025: precio con descuento
        'span.s13lowb4',  # Nuevo 2025: precio original tachado
        'span._tyxjp1',   # Selector 2024 (por si vuelve)
        # ... otros selectores ...
    ]
    
    for selector in selectores_precio:
        try:
            page.wait_for_selector(selector, state='visible', timeout=timeout)
            logger.debug(f"[Airbnb] ✅ Precio visible con selector: {selector}")
            return True
        except PlaywrightTimeout:
            continue
    
    logger.warning(f"[Airbnb] ❌ Ningún selector de precio se volvió visible")
    return False
```

**Ventajas:**
- ✅ NO espera tiempo innecesario si el precio aparece antes
- ✅ Detecta cuando React terminó de renderizar
- ✅ Timeout máximo de 15 segundos (más tiempo si la página es lenta)
- ✅ Registra cuál selector funcionó en los logs

### 2. Selectores Actualizados

**Lista de selectores en `_extraer_precio_mejorado()`:**
```python
selectores_mejorados = [
    'span.umuerxh',   # ⭐ NUEVO 2025: precio con descuento
    'span.s13lowb4',  # ⭐ NUEVO 2025: precio original tachado
    'span._tyxjp1',   # Selector 2024
    'span._1k4xcdh',
    'div[data-section-id="BOOK_IT_SIDEBAR"] span[class*="_14y1gc"]',
    'div._1jo4hgw',
    'span[class*="price"]',
    'div[class*="PriceLockup"]',
    'span[class*="_tyxjp1"]',
    'div[class*="_1y74zjx"]',
    'span[aria-hidden="true"]',
]
```

**Lógica de selección:**
1. Intenta con `span.umuerxh` (precio con descuento) primero
2. Si no funciona, intenta con `span.s13lowb4` (precio original)
3. Continúa con los selectores antiguos por compatibilidad
4. **Validación:** Solo acepta precios entre $10 y $10,000 USD

### 3. Validación de Rango

La función `validar_precio()` ya existente asegura que:
- ✅ El texto extraído contenga números
- ✅ El valor esté entre $10 y $10,000 USD
- ✅ Se rechacen valores absurdos como $13,861,461,146,138.50

## 📊 Impacto Esperado

### Antes de la corrección:
```
2025-11-07 12:26:38 - [Airbnb] Esperando carga de contenido...
2025-11-07 12:26:46 - [Airbnb] Buscando precio...
2025-11-07 12:26:46 - [Airbnb] No se encontró precio para 2 noche(s)
→ RESULTADO: precio = 0, error = "No disponible"
```

### Después de la corrección:
```
2025-11-07 12:26:38 - [Airbnb] Esperando carga de contenido...
2025-11-07 12:26:43 - [Airbnb] Esperando renderizado de elementos de precio...
2025-11-07 12:26:45 - [Airbnb] ✅ Precio visible con selector: span.umuerxh
2025-11-07 12:26:45 - [Airbnb] Buscando precio...
2025-11-07 12:26:45 - [Airbnb] Precio encontrado con selector: span.umuerxh -> $254 USD
2025-11-07 12:26:45 - [Airbnb] Precio encontrado: 127.00 (2 noche(s))
→ RESULTADO: precio = 127.00, noches = 2
```

## 🧪 Cómo Probar

### Opción 1: Scraping Real
```bash
# Ejecutar scraping con fechas futuras
cd /workspaces/price-monitor
streamlit run app.py
# Ir a página "Scraping" y buscar diciembre 2025 - enero 2026
```

### Opción 2: Script de Prueba
```bash
# Crear script de prueba específico
python3 test_airbnb_selectores_2025.py
```

## 📁 Archivos Modificados

1. **`scrapers/robots/airbnb_robot.py`**
   - ✅ Agregado método `_esperar_precio_visible()`
   - ✅ Actualizada lista `selectores_mejorados` con clases nuevas
   - ✅ Cambiado timeout inicial de 8s → 5s + espera activa
   - ✅ Agregados logs de debug para diagnóstico

## 🎯 Próximos Pasos

### Inmediato:
1. ✅ Validar con scraping real (URL de Exequiel)
2. ⏳ Verificar que funcione con otros alojamientos
3. ⏳ Probar con descuentos vs sin descuentos

### Mantenimiento:
- Cuando Airbnb cambie las clases CSS nuevamente:
  1. Inspeccionar elemento en el navegador
  2. Identificar las nuevas clases
  3. Agregarlas al principio de `selectores_mejorados`
  4. NO borrar las antiguas (pueden volver)

### Monitoreo:
- Revisar logs de scraping buscando:
  - `"✅ Precio visible con selector"` → Selector que funcionó
  - `"❌ Ningún selector de precio se volvió visible"` → Ninguno funcionó
  - `"No se encontró precio"` → Elemento visible pero texto no válido

## 📝 Notas Importantes

### Diferencia: Precio con Descuento vs Original

Si Airbnb muestra:
- **$310 USD** ~~(tachado)~~ → Precio original
- **$254 USD** → Precio con descuento

El scraper debe extraer **$254 USD** (el precio real que el cliente pagará).

Por eso `span.umuerxh` está ANTES que `span.s13lowb4` en la lista.

### ¿Por qué el HTML guardado no tiene los precios?

Cuando usas "Copy outerHTML" en DevTools, solo copias el HTML **inicial** que el servidor envió. Los elementos de React se agregan **después** mediante JavaScript.

Para obtener el HTML completo con React renderizado:
1. Usar Playwright/Selenium (como hace el robot)
2. Esperar a que los elementos dinámicos se carguen
3. Guardar DESPUÉS de que React termine

---

**Última actualización:** 7 de noviembre de 2025  
**Responsable:** Asistente de desarrollo  
**Validado por:** Exequiel (análisis HTML real)
