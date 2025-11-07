# VERSIONAMIENTO – Estrategia Semántica

## 1. Objetivo
Definir esquema consistente para etiquetar releases y comunicar cambios.

## 2. Convención SemVer
`MAJOR.MINOR.PATCH`  
- MAJOR: Cambios incompatibles (schema BD, contrato robot).  
- MINOR: Funcionalidad nueva retrocompatible (nuevo robot, métricas).  
- PATCH: Correcciones y optimizaciones menores.  

## 3. Tags Retroactivos Propuestos
| Tag | Commit | Descripción |
|-----|--------|-------------|
| v1.0.0 | 8d63375 | MVP inicial completo |
| v1.1.0 | 89004ad | Config VSCode + tests + docs básicas |
| v1.2.0 | da7e904 | Mejora scraping + Expedia soporte |
| v1.3.0 | 8c89ab3 | Sistema eliminación datos |
| v1.3.1 | 79c8b0b | Fix session state |
| v3.0.0 | (merge V3) | Arquitectura nueva + constitución |

## 4. Proceso Release
1. Crear rama `release/vX.Y.Z`.  
2. Ejecutar checklist (tests, quality, docs).  
3. Generar changelog.  
4. Crear tag anotado: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.  
5. Push tags: `git push --tags`.  
6. Publicar resumen en README / CHANGELOG.  

## 5. Changelog (Formato)
```
## [v1.3.1] - 2025-11-07
### Fixed
- Corregido error de session_state en eliminación de datos.
```

## 6. Branching Model
- `main`: estable.  
- `develop` (opcional): integración continua.  
- `feature/*`: nuevas funcionalidades.  
- `hotfix/*`: correcciones críticas sobre tag.  

## 7. Deuda Técnica y Versiones
Cada issue de deuda incluye campo `target_version` para seguimiento.  

## 8. Herramienta de Automatización (Futuro)
Script `bump_version.py` para actualizar tag y generar changelog parcial.

---
Fin del documento de versionamiento.
