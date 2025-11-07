# Visión del Negocio (V3)

Fecha: 2025-11-07

## Propósito
Construir un sistema de inteligencia de precios y disponibilidad para alojamientos que permita:
- Monitorear precios y ocupación históricamente por establecimiento y plataforma.
- Detectar cambios, oportunidades y anomalías en tiempo casi real.
- Sustentar decisiones de revenue con datos confiables, auditables y reproducibles.

## Objetivos de negocio
- Reducir el tiempo de obtención de datos (TtD) y aumentar la cobertura de plataformas.
- Minimizar falsos positivos/negativos en precios y disponibilidad.
- Aumentar la resiliencia ante cambios (DOM, anti-bot, políticas).

## Métricas clave (KPIs)
- Tasa de éxito de scraping por plataforma (%)
- Latencia promedio por URL (s)
- Porcentaje de precios inválidos/outliers rechazados (%)
- Frescura de datos (<48h) por establecimiento (%)
- Tiempo de incorporación de una nueva plataforma (h)

## Alcance
- V3 se enfoca en un pipeline modular y observable, con datos raw y normalizados, y UI desacoplada.
- Se preserva la entidad Establecimientos como núcleo.

## Principios guía
- Modularidad y apertura a nuevas fuentes (scraping/APIs/manual).
- Observabilidad por defecto (eventos, métricas, logs).
- Memoria histórica: lecciones V1/V2 integradas en cada fase.

## Roadmap por fases (resumen)
- Fase 0: Constitución y migración V1→V3.
- Fase 1: Datos y dominio.
- Fase 2: Ingesta y scraping (SDK robots y fallback multi-estrategia).
- Fase 3: Persistencia y normalización.
- Fase 4: Observabilidad y testing.
- Fase 5: UI y API.
- Fase 6: Seguridad y operación.
