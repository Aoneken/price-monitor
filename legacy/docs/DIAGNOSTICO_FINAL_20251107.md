# INFORME DE DIAGNÓSTICO - Sistema Price Monitor
**Fecha:** 7 de noviembre, 2025  
**Estado:** PROBLEMA CRÍTICO IDENTIFICADO

---

## 🔴 PROBLEMA PRINCIPAL

**El sistema NO está guardando precios en la base de datos porque los robots de scraping NO están encontrando precios en las páginas web.**

### Evidencia:
- ✅ Base de datos funciona correctamente (inserción manual probada y exitosa)
- ✅ Orquestador funciona y llama a `_guardar_resultado()`
- ✅ URLs activas: 27 URLs configuradas en la BD
- ❌ **0 precios guardados** en todos los scrapings
- ❌ Logs muestran: `"No disponible para ninguna duración (3, 2, 1 noches)"` repetidamente

---

## 🔍 ANÁLISIS DETALLADO

### 1. **Selectores CSS Desactualizados**
Airbnb cambió su estructura HTML recientemente (nov 2025). Los selectores actuales:
- `span._tyxjp1` ❌
- `span.umuerxh` ❌  
- `span.s13lowb4` ❌

**Ninguno de estos selectores existe en el HTML real capturado.**

### 2. **Estrategias de Extracción Insuficientes**
- El robot actual depende 100% de selectores CSS
- No extrae desde JSON embebido (Apollo State, Next Data)
- No hay fallback robusto cuando los selectores fallan

### 3. **Tiempos de Espera Excesivos**
- Espera 3-10 segundos para "renderizado"
- Airbnb es una SPA (Single Page Application) con React
- La página puede parecer "cargada" pero el contenido de precio tarda más

### 4. **Problema de Disponibilidad Real**
Es posible que algunas fechas realmente NO estén disponibles, pero el robot no puede distinguir entre:
- "No disponible porque está ocupado"
- "No disponible porque no puedo extraer el precio"

---

## 💡 SOLUCIONES IMPLEMENTADAS

### ✅ Robot Airbnb V2 Creado
**Archivo:** `scrapers/robots/airbnb_robot_v2.py`

**Mejoras:**
1. **Extracción desde JSON embebido** (primera estrategia)
2. **Múltiples estrategias de fallback**:
   - JSON en `<script>` tags
   - Selectores CSS actualizados
   - Regex sobre texto completo
3. **Espera reducida** (2s en lugar de 10s)
4. **Validación estricta** de precios (rango $10-$10,000)
5. **Debug mejorado** (screenshots + HTML)

### ⚠️ Limitación Detectada
Los tests con Robot V2 siguen sin encontrar precios. Posibles causas:
1. **Airbnb requiere cookies/sesión** activa
2. **Detección de bot** más sofisticada
3. **Las fechas específicas realmente no están disponibles**

---

## 🎯 RECOMENDACIONES INMEDIATAS

### **OPCIÓN A: Enfoque Manual de Validación** (MÁS RÁPIDO)
1. **Verificar manualmente** si las URLs tienen precios disponibles:
   ```bash
   # Abrir en navegador normal
   https://www.airbnb.es/rooms/[ID]?checkin=2025-11-08&checkout=2025-11-10
   ```
   
2. Si hay precios visibles:
   - Tomar screenshots
   - Inspeccionar HTML real
   - Identificar selectores exactos
   - Actualizar `airbnb_robot_v2.py`

3. Si NO hay precios:
   - **Las fechas están realmente no disponibles**
   - Probar con fechas futuras (diciembre 2025)

### **OPCIÓN B: Cambio de Estrategia Técnica** (MÁS ROBUSTO)
1. **Usar Selenium en lugar de Playwright**
   - Algunos sitios detectan Playwright más fácil
   
2. **Implementar cookies reales**
   - Copiar cookies de sesión del navegador
   - Pasar al robot para simular sesión humana

3. **Proxy/VPN** si hay bloqueo geográfico

### **OPCIÓN C: API Alternativa** (MÁS CONFIABLE)
Considerar servicios de scraping especializados:
- **ScraperAPI** ($49/mes, 100k requests)
- **Bright Data** (desde $500/mes, enterprise)
- **Apify Airbnb Actor** ($0.0015 per listing)

---

## 📋 PRÓXIMOS PASOS SUGERIDOS

### Inmediato (Hoy):
1. ✅ **Ejecutar verificación manual**:
   ```bash
   # Test con fecha futura
   python test_robot_v2_rapido.py
   ```
   - Cambiar fecha a diciembre 2025
   - Ver si encuentra precios

2. ✅ **Revisar un establecimiento específico** en navegador normal
   - Verificar que tiene precios visibles
   - Tomar screenshot del HTML inspector
   - Extraer selectores exactos

3. ✅ **Actualizar selectores** basado en hallazgos

### Corto Plazo (Esta Semana):
4. **Implementar sistema de cookies**
   - Archivo: `scrapers/utils/cookie_manager.py`
   - Permite usar cookies de sesión real

5. **Agregar modo "debug interactivo"**
   - Ver el navegador mientras scrapea
   - Pausar para inspección manual

6. **Implementar rate limiting inteligente**
   - Espaciar requests más (30-60s entre páginas)
   - Rotar user agents

### Mediano Plazo (Próximos 15 Días):
7. **Considerar solución híbrida**:
   - Usar robot propio para Booking/Expedia
   - Usar API de terceros solo para Airbnb

8. **Implementar alertas**:
   - Email cuando scraping falla X veces seguidas
   - Webhook a Discord/Slack con capturas

9. **Dashboard de monitoreo**:
   - Tasa de éxito por plataforma
   - Últimos precios obtenidos
   - Estado de URLs activas

---

## 📊 MÉTRICAS ACTUALES

| Métrica | Valor | Estado |
|---------|-------|--------|
| Establecimientos | 13 | ✅ OK |
| URLs Activas | 27 | ✅ OK |
| Precios Guardados | **0** | 🔴 CRÍTICO |
| Tasa de Éxito | **0%** | 🔴 CRÍTICO |
| Último Scraping Exitoso | Nunca | 🔴 CRÍTICO |

---

## 🛠️ ARCHIVOS MODIFICADOS/CREADOS

1. ✅ `test_diagnostico_urgente.py` - Diagnóstico completo del sistema
2. ✅ `scrapers/robots/airbnb_robot_v2.py` - Robot mejorado con múltiples estrategias
3. ✅ `scrapers/robot_factory.py` - Actualizado para usar V2
4. ✅ `test_robot_v2_rapido.py` - Test específico del robot V2

---

## 💬 MENSAJE PARA EL USUARIO

**La buena noticia:** El sistema está bien diseñado y la infraestructura funciona.

**El desafío:** Airbnb (y plataformas similares) están constantemente actualizando sus medidas anti-bot. Esto es un juego del gato y el ratón.

**Recomendación práctica:** 
1. Probar primero con fechas más lejanas (ej: enero-febrero 2026)
2. Verificar manualmente que haya disponibilidad en las URLs configuradas
3. Si persiste el problema, considerar usar una API de terceros para Airbnb específicamente

**Costo-beneficio:**
- Desarrollo continuo de bypass: ~10-20 horas/mes de mantenimiento
- API de terceros: $50-100/mes sin mantenimiento

¿Qué enfoque prefieres para seguir adelante?
