# 📋 Índice de Documentación V3

Este directorio contiene toda la documentación técnica del proyecto Price Monitor V3.

## 📚 Estructura

### 📖 Documentos por Fases

Documentación técnica organizada por etapas de desarrollo:

1. **[FASE_0_CONSTITUCION_Y_MIGRACION.md](FASE_0_CONSTITUCION_Y_MIGRACION.md)**
   - Motivación y lecciones de V1/V2
   - Principios arquitectónicos V3
   - Plan de migración
   - Preservación del legado

2. **[FASE_1_DATOS_Y_DOMINIO.md](FASE_1_DATOS_Y_DOMINIO.md)**
   - Modelo de dominio
   - Contratos de datos (Quote objects)
   - Schema de base de datos
   - Validaciones y constraints

3. **[FASE_2_INGESTA_Y_SCRAPING.md](FASE_2_INGESTA_Y_SCRAPING.md)**
   - Arquitectura de scraping
   - Parsers por plataforma
   - Robots con Playwright
   - Manejo de errores y reintentos

4. **[FASE_3_PERSISTENCIA_Y_NORMALIZACION.md](FASE_3_PERSISTENCIA_Y_NORMALIZACION.md)**
   - DatabaseAdapter
   - Normalización de datos
   - Sistema de caché
   - Transacciones y concurrencia

5. **[FASE_4_OBSERVABILIDAD_Y_TESTING.md](FASE_4_OBSERVABILIDAD_Y_TESTING.md)**
   - Estrategia de testing
   - Logging estructurado
   - Métricas y monitoreo
   - Debugging

6. **[FASE_5_UI_Y_API.md](FASE_5_UI_Y_API.md)**
   - Interfaz Streamlit
   - Páginas y componentes
   - Flujos de usuario
   - API futura (roadmap)

7. **[FASE_6_SEGURIDAD_Y_OPERACION.md](FASE_6_SEGURIDAD_Y_OPERACION.md)**
   - Consideraciones de seguridad
   - Anti-detección
   - Rate limiting
   - Deploy y operación

### 🎯 Visión y Estrategia

- **[VISION_NEGOCIO_V3.md](VISION_NEGOCIO_V3.md)**: Visión de negocio, objetivos y casos de uso
- **[RESUMEN_METODOLOGIAS_Y_TESTS.md](RESUMEN_METODOLOGIAS_Y_TESTS.md)**: Resumen ejecutivo de metodologías y suite de tests

### 🏢 Documentos Ejecutivos

Directorio `executive/` con resúmenes de alto nivel:

- **[RESUMEN_FINAL_V3.txt](executive/RESUMEN_FINAL_V3.txt)**: Documento ejecutivo de cierre del proyecto
- **[SISTEMA_V3_COMPLETO.md](executive/SISTEMA_V3_COMPLETO.md)**: Visión completa del sistema
- **[MEJORAS_UX_V3.md](executive/MEJORAS_UX_V3.md)**: Mejoras de experiencia de usuario implementadas
- **[IMPLEMENTACION_SDK_V3_COMPLETA.md](executive/IMPLEMENTACION_SDK_V3_COMPLETA.md)**: Resumen técnico de implementación del SDK

### 🔬 Metodologías por Plataforma

Directorio `metodologias/` con detalles de scraping:

- **[METODOLOGIA_AIRBNB.md](metodologias/METODOLOGIA_AIRBNB.md)**: Extracción de datos de Airbnb
  - Estrategias de parsing
  - Selectores CSS
  - JSON-LD y structured data
  - Casos edge

- **[METODOLOGIA_BOOKING.md](metodologias/METODOLOGIA_BOOKING.md)**: Extracción de datos de Booking
  - JSON embebido
  - Fallbacks del DOM
  - Manejo de impuestos
  - Casos edge

- **[METODOLOGIA_EXPEDIA.md](metodologias/METODOLOGIA_EXPEDIA.md)**: Extracción de datos de Expedia
  - Detección de descuentos
  - Precios tachados
  - Structured data
  - Casos edge

### 📊 Resultados de Exploración

Resultados de investigación inicial de cada plataforma:

- **[RESULTADOS_EXPLORACION_AIRBNB.md](metodologias/RESULTADOS_EXPLORACION_AIRBNB.md)**
- **[RESULTADOS_EXPLORACION_BOOKING.md](metodologias/RESULTADOS_EXPLORACION_BOOKING.md)**
- **[RESULTADOS_EXPLORACION_EXPEDIA.md](metodologias/RESULTADOS_EXPLORACION_EXPEDIA.md)**

### 🛠️ Documentación del SDK

- **[SDK_V3_README.md](SDK_V3_README.md)**: Documentación completa del SDK con ejemplos de código

## 🚀 Inicio Rápido

### Para Usuarios

1. Lee **[VISION_NEGOCIO_V3.md](VISION_NEGOCIO_V3.md)** para entender qué hace el sistema
2. Revisa el **[README.md](../README.md)** principal para instrucciones de instalación
3. Consulta **[executive/MEJORAS_UX_V3.md](executive/MEJORAS_UX_V3.md)** para entender las funcionalidades

### Para Desarrolladores

1. Lee **[FASE_0_CONSTITUCION_Y_MIGRACION.md](FASE_0_CONSTITUCION_Y_MIGRACION.md)** para contexto histórico
2. Estudia **[FASE_1_DATOS_Y_DOMINIO.md](FASE_1_DATOS_Y_DOMINIO.md)** para entender el modelo de datos
3. Revisa **[SDK_V3_README.md](SDK_V3_README.md)** para trabajar con el código
4. Consulta **[metodologias/](metodologias/)** para detalles de scraping por plataforma

### Para Gestión

1. Lee **[executive/RESUMEN_FINAL_V3.txt](executive/RESUMEN_FINAL_V3.txt)** para visión ejecutiva
2. Revisa **[executive/SISTEMA_V3_COMPLETO.md](executive/SISTEMA_V3_COMPLETO.md)** para arquitectura general
3. Consulta **[VISION_NEGOCIO_V3.md](VISION_NEGOCIO_V3.md)** para objetivos de negocio

## 📖 Flujo de Lectura Recomendado

### Nivel Principiante
```
README.md → VISION_NEGOCIO_V3.md → SDK_V3_README.md → Metodologías
```

### Nivel Intermedio
```
FASE_0 → FASE_1 → FASE_2 → SDK_V3_README.md → Tests
```

### Nivel Avanzado
```
executive/SISTEMA_V3_COMPLETO.md → Todas las Fases → Metodologías → Código fuente
```

## 🔗 Enlaces Útiles

- **Repositorio**: [GitHub](https://github.com/Aoneken/price-monitor)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)
- **Tests**: [tests_v3/README.md](../tests_v3/README.md)
- **Scripts**: [scripts/](../scripts/)

## 📝 Convenciones

### Formato de Documentos

- **Markdown** estándar con extensiones GitHub
- **Secciones numeradas** para fases técnicas
- **Emojis** para mejorar legibilidad
- **Bloques de código** con syntax highlighting

### Nomenclatura

- `FASE_N_NOMBRE.md`: Documentación técnica por fase
- `METODOLOGIA_PLATAFORMA.md`: Detalles de scraping
- `RESULTADOS_EXPLORACION_PLATAFORMA.md`: Investigación inicial
- `RESUMEN_*.md/.txt`: Documentos ejecutivos

## 🆘 Soporte

Para preguntas sobre la documentación:

1. Revisa primero el documento relevante
2. Busca en issues de GitHub
3. Crea un nuevo issue con etiqueta `documentation`

---

**Última actualización**: 2025-11-07  
**Versión**: 3.0.0  
**Mantenedor**: Aoneken
