# SEGURIDAD & CUMPLIMIENTO V3

## 1. Objetivo
Garantizar uso responsable del scraping, protección de datos y mitigación de riesgos legales.

## 2. Principios
- Mínimo privilegio en accesos.  
- Transparencia sobre fuentes y limitaciones.  
- Separar credenciales, no almacenarlas en repo.  

## 3. Datos Sensibles
| Tipo | Medida |
|------|--------|
| Credenciales Proxy | Vault / env vars |
| Tokens API FX | `.env` excluido de Git |
| Logs HTML | Sanitizar (remover tokens) |

## 4. Scraping Responsable
- Delays aleatorios y límites de concurrencia.  
- Respetar términos legales (no extracción masiva ilícita).  
- Posibilidad de migrar a acuerdos de datos oficiales (APIs).  

## 5. Auditoría
- Registro de cada ejecución robot con timestamp y resultado.  
- Hash HTML para detectar manipulación.  

## 6. Riesgos Legales
| Riesgo | Acción |
|--------|--------|
| Terms of Service Violación | Documentar casos, evaluar API alterna |
| Bloqueo IP | Rotación controlada, no evasión agresiva |
| Uso indebido datos | Aislar entorno interno, no publicar externamente |

## 7. Gestión de Incidentes
1. Detectar evento crítico (bloqueo masivo, leak).  
2. Registrar incidente `event_log`.  
3. Notificación interna (email/slack).  
4. Plan de contención (pause tasks).  

## 8. Caducidad Datos
- Retención 18 meses observaciones crudas.  
- Resumen estadístico conservado después.  

## 9. Hardening (Futuro)
- Contenedores sin root.  
- Escaneo dependencias (pip-audit).  
- Limitar permisos de red (salidas solo a dominios necesarios).  

## 10. Privacidad
No se captura PII de usuarios finales; sólo datos públicos de anuncios.  

## 11. Checklist Seguridad Release
- [ ] No credenciales en Git.  
- [ ] Dependencias escaneadas.  
- [ ] Logs sin PII.  
- [ ] Módulos scraping con límites configurados.  

---
Fin del documento seguridad V3.
