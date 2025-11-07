# Fase 0 – Constitución y Migración V1→V3

## Objetivo
Establecer los principios rectores, consolidar lecciones heredadas y migrar a un esqueleto limpio manteniendo Establecimientos.

## Entregables
- Constitución condensada (principios, riesgos, no-funcionales).
- Esqueleto V3 con `Establecimientos` y `db_manager` mínimo.
- Documentación de lecciones heredadas integrada.
- Tags y versionamiento (v3.0.0).

## Criterios de aceptación
- docs_v3 contiene solo Visión y documentos por fase.
- Código legado en `legacy/` y raíz limpia.
- Tag `v3.0.0` creado.

## Lecciones heredadas (síntesis)
- No depender sólo de parámetros en URL (Airbnb); soportar interacción/variantes/API.
- Validar precios con políticas y rechazar outliers.
- Diferenciar estados de error vs no disponibilidad.

## Riesgos y mitigación
- Pérdida de contexto → Todo legado preservado en `legacy/` y en historial git.
- Ruptura de compatibilidad → Reconstrucción por fases con contratos.
