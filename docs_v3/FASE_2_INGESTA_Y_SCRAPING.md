# Fase 2 – Ingesta y Scraping

## Objetivo
Construir un SDK de robots con estrategias de extracción múltiples y contrato uniforme.

## Alcance
- AbstractRobotV3: interfaz única.
- ExtractionEngine: DOM + JSON embebido + API intercept + regex.
- Navigator: interacción (selección de fechas) cuando URL no aplica.
- SelectorRegistry: versionado y fallback de selectores.

## Criterios de aceptación
- Robot de Airbnb con interacción/fallback operativa.
- Eventos de scraping: intentos, fallos con códigos, éxitos.
- Métrica de tasa de éxito por plataforma.

## Lecciones heredadas relevantes
- Airbnb ignorando parámetros de fecha → Interacción o API.
- Selectores frágiles → Estrategias alternativas y health-check de selectores.
- Diferenciar "no disponible" de "error extracción".
