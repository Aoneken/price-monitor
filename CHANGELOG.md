# Changelog

Todos los cambios notables del proyecto Price Monitor se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-11-07

### 🎯 Versión Mayor - Reescritura Completa V3

Esta versión representa una reescritura completa del sistema con arquitectura modular y SDK consolidado.

### ✨ Agregado

#### SDK V3 Completo
- **Parsers modulares** por plataforma (Airbnb, Booking, Expedia)
- **Robots con Playwright** y configuración stealth anti-detección
- **Normalizers** para validación y normalización de datos multi-divisa
- **Orchestrator** para coordinación multi-plataforma
- **Quality scoring** (0-1) basado en confiabilidad de la fuente de datos
- **Manejo robusto de errores** con códigos específicos por plataforma

#### Interfaz de Usuario (Streamlit)
- **Página Scraping V3** (página 6):
  - Configuración en línea compacta (4 columnas)
  - Selector de fechas personalizado (inicio/fin)
  - Cálculo automático de noches
  - Filtros inteligentes por plataforma, establecimiento y URLs específicas
  - Progress bar con nombre de establecimiento
  - Métricas compactas (Total, Filtradas, Pendientes, En caché)
  
- **Página Monitoreo V3** (página 7):
  - Métricas generales en tiempo real
  - Distribución de URLs con datos por plataforma
  - Actividad reciente (50 últimos scrapeos)
  - Gráficos de tendencias históricas (30 días)
  - Sistema anti-parpadeo con altura fija en tablas
  - Botón de actualización manual con caché de 60 segundos
  
- **Página Gestión URLs** (página 8):
  - CRUD completo de establecimientos
  - Agregar, activar/desactivar, eliminar URLs
  - Interfaz con tabs y expanders
  - Nombres de establecimientos en filtros

#### Sistema de Caché
- Caché inteligente configurable (default 24h)
- Evita re-scraping innecesario
- Métricas de hits/misses
- Forzar re-scraping cuando sea necesario

#### Automatización
- **Scheduler CLI** (`scripts/scheduler_v3.py`):
  - Ejecución batch desde terminal
  - Filtrado por plataforma
  - Configuración flexible (días adelante, noches, caché)
  - Logging completo en `logs/scheduler_v3.log`
  - Límite de URLs procesables
  - Modo headless configurable

#### Testing
- **26+ tests unitarios** para parsers (Airbnb, Booking, Expedia)
- Tests de integración rápidos
- Fixtures HTML para testing offline
- Scripts de validación con URLs reales
- Demo del SDK sin navegación

#### Documentación
- Documentación completa en `docs_v3/`
- Metodologías detalladas por plataforma
- Documentos ejecutivos en `docs_v3/executive/`
- README consolidado con guía completa
- SDK README con ejemplos de código

### 🔧 Cambiado

#### Arquitectura
- Migración de código legacy V1/V2 a carpeta `legacy/`
- Separación clara de responsabilidades (parsers/robots/normalizers)
- Contratos de datos bien definidos (AirbnbQuote, BookingQuote, ExpediaQuote)
- Flujo de datos unidireccional y predecible

#### Base de Datos
- Schema optimizado con índices
- Mejor tracking de errores
- Timestamps precisos para caché
- Campos adicionales para quality scoring

#### UI/UX
- Diseño compacto sin scrolls innecesarios
- Filtros inteligentes que respetan selecciones de plataforma
- Vista sin sidebar para más espacio
- Métricas en tiempo real sin refresco automático
- Sistema anti-parpadeo en tablas

### 🐛 Corregido

- **Parser Booking**: Extracción correcta de precio desde JSON embebido
- **Robots**: Extracción de HTML completo (no solo fragmentos)
- **URLs**: Corrección de URLs en BD (Viento de Glaciares)
- **Filtros**: Filtros inteligentes que solo muestran establecimientos con URLs en plataformas seleccionadas
- **Parpadeo**: Altura fija en tablas (`height=400` y `height=200`)
- **Comparaciones**: Uso de `pd.notna()` en lugar de comparación directa con None
- **Cache**: Cálculo correcto de frescura de datos

### 📝 Documentos Agregados

- `docs_v3/FASE_0_CONSTITUCION_Y_MIGRACION.md`
- `docs_v3/FASE_1_DATOS_Y_DOMINIO.md`
- `docs_v3/FASE_2_INGESTA_Y_SCRAPING.md`
- `docs_v3/FASE_3_PERSISTENCIA_Y_NORMALIZACION.md`
- `docs_v3/FASE_4_OBSERVABILIDAD_Y_TESTING.md`
- `docs_v3/FASE_5_UI_Y_API.md`
- `docs_v3/FASE_6_SEGURIDAD_Y_OPERACION.md`
- `docs_v3/RESUMEN_METODOLOGIAS_Y_TESTS.md`
- `docs_v3/VISION_NEGOCIO_V3.md`
- `docs_v3/metodologias/METODOLOGIA_AIRBNB.md`
- `docs_v3/metodologias/METODOLOGIA_BOOKING.md`
- `docs_v3/metodologias/METODOLOGIA_EXPEDIA.md`
- `docs_v3/metodologias/RESULTADOS_EXPLORACION_*.md`
- `docs_v3/executive/RESUMEN_FINAL_V3.txt`
- `docs_v3/executive/SISTEMA_V3_COMPLETO.md`
- `docs_v3/executive/MEJORAS_UX_V3.md`
- `docs_v3/executive/IMPLEMENTACION_SDK_V3_COMPLETA.md`

### 🔬 Tests Validados

- ✅ Test Booking: US$650 (2 noches × $325/noche) - Viento de Glaciares
- ✅ Suite completa de parsers con fixtures HTML
- ✅ Tests de integración con orchestrator
- ✅ Validación de normalización multi-divisa

### 📊 Métricas de Calidad

- **Cobertura de tests**: Parsers al 100%
- **Tests passing**: 26/26 (100%)
- **Plataformas soportadas**: 3 (Airbnb, Booking, Expedia)
- **Establecimientos en BD**: 13
- **URLs monitoreadas**: 27

---

## [2.x] - Legacy

Versiones anteriores (V1/V2) han sido movidas a la carpeta `legacy/` para referencia histórica.

### Características Legacy
- Scraping básico de Booking y Airbnb
- UI Streamlit inicial
- Base de datos SQLite básica
- Sistema de selectores CSS configurables
- Lógica 3→2→1 noches
- Frescura de datos 48h

### Lecciones Aprendidas (V1/V2)

Documentadas en `docs_v3/FASE_0_CONSTITUCION_Y_MIGRACION.md`:

1. **Selectores frágiles**: Los selectores CSS cambian frecuentemente
2. **Monolitos**: Código acoplado difícil de mantener y testear
3. **Sin contracts**: Ausencia de validación de datos
4. **Testing manual**: No había tests automatizados
5. **Logging insuficiente**: Difícil diagnosticar errores en producción
6. **Sin caché**: Re-scraping innecesario y costoso
7. **UI monolítica**: Todo en una sola página, difícil de navegar

Estas lecciones guiaron el diseño de V3.

---

## Tipos de Cambios

- **Agregado**: Nuevas características
- **Cambiado**: Cambios en funcionalidad existente
- **Obsoleto**: Características que serán removidas
- **Removido**: Características removidas
- **Corregido**: Corrección de bugs
- **Seguridad**: Vulnerabilidades corregidas

---

## Convenciones de Commits

Este proyecto usa commits semánticos:

- `feat:` Nueva característica
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formateo, punto y coma faltantes, etc.
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Mantenimiento, dependencias, etc.

---

## Links

- [Repositorio](https://github.com/Aoneken/price-monitor)
- [Issues](https://github.com/Aoneken/price-monitor/issues)
- [Documentación V3](docs_v3/)

---

**Versión actual**: 3.0.0  
**Branch principal**: v3  
**Status**: ✅ Producción Ready
