# Visión del producto — Price Monitor

Fecha: 2025-11-09

## Propósito

Facilitar a gestores de alojamientos y analistas el monitoreo histórico de precios y disponibilidad, permitiendo comparar evolución y generar reportes reproducibles. Todo en entorno local y extensible.

## Usuarios objetivo

- Gestores y operadores de alojamientos.
- Analistas técnicos orientados a pricing / revenue.
- Desarrolladores que agregan nuevos providers o integran datos en BI local.

## Principios de producto

- Local-first: puede ejecutarse completo en una máquina sin servicios externos.
- Reproducibilidad: mismo scrape produce mismos datos dado mismo rango y parámetros.
- Extensibilidad: agregar un provider nuevo requiere implementar una interfaz clara (ver `ARCHITECTURE.md`).
- Transparencia operacional: progreso visible en tiempo real y export simple (CSV/JSON).

## Diferenciadores clave

- Un único core reutilizado por CLI y webapp (menor duplicación, menor mantenimiento).
- Modelo de datos preparado para evolución futura (seasons, workspaces, snapshots).

## Alcance actual vs futuro

- Actual: scraping de Airbnb, visualización básica y exportaciones locales.
- Futuro (prioridades): más providers, métricas operacionales, migraciones formales, cola de jobs.

## Referencias

- Arquitectura técnica: `ARCHITECTURE.md`.
- Estado y roadmap: `PROJECT_STATUS.md`.
- Uso e instalación: `README.md`.

Esta visión guía decisiones de priorización. Cambios estratégicos deben reflejarse aquí y luego impactar en el estado técnico y la arquitectura.
