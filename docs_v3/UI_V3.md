# UI V3 – Diseño de Presentación

## 1. Objetivo
Evolucionar la UI de Streamlit hacia una capa desacoplada con posibilidad futura de migrar a un frontend especializado (React + API REST). Mientras tanto, optimizar ergonomía y observabilidad.

## 2. Principios
- "Estado mínimo": UI no guarda lógica crítica; usa servicios.  
- Feedback inmediato: cada acción emite estado y progreso.  
- Accesibilidad básica: etiquetas claras, contraste adecuado.  
- Navegación por tareas: en vez de pestañas rígidas, secciones funcionales.  

## 3. Páginas Propuestas
| Página | Función |
|--------|--------|
| Inicio | Overview métricas clave, estado robots |
| Establecimientos | CRUD + gestión listing y salud plataforma |
| Monitoreo | Lanzar tareas, ver cola, cancelar, reintentar |
| Datos | Exploración avanzada (filtros compuestos, export) |
| Dashboard | Agregaciones y comparativas multi-plataforma |
| Eventos | Lista de eventos (bloqueos, anomalías, actualizaciones) |
| Configuración | Selectores, parámetros scraping, monedas |
| Análisis (futuro) | Recomendaciones, benchmarking extendido |

## 4. Componentes Reutilizables
| Componente | Descripción |
|------------|-------------|
| TaskLauncher | Formulario + validación + emisión evento |
| ProgressStream | Suscripción a eventos de progreso |
| PriceTable | Tabla normalizada con columnas dinámicas |
| MetricsHeader | KPIs con actualización en vivo |
| EventFeed | Stream de eventos con filtros |
| SelectorManager | Cargar/ver/validar versiones selectores |

## 5. Estado y Comunicación
- Polling inicial (cada 5s) → transicionar a websockets / Server-Sent Events.  
- Estado global mínimo: tasks en curso, últimos KPIs, mapa plataformas.  

## 6. Indicadores UX
| Indicador | Objetivo |
|-----------|---------|
| Tiempo hasta feedback | < 1s tras lanzar tarea |
| Claridad de error | Mensaje + código + acción sugerida |
| Profundidad de navegación | Máximo 2 niveles |

## 7. Visualizaciones Clave
- Serie temporal precio normalizado vs ocupación.  
- Heatmap disponibilidad (matriz fecha vs listing).  
- Boxplot multi-plataforma.  
- Gráfico eventos bloqueos por hora.  

## 8. Optimización Performance
- Cargar datos paginados (lazy).  
- Evitar recalcular gráficos completos si no cambian filtros.  
- Uso de vistas materializadas para queries pesadas.  

## 9. Tematización
- Paleta neutra + acentos por plataforma.  
- Estados: verde (éxito), amarillo (retry), rojo (bloqueo), gris (inactivo).  

## 10. Ejemplo de API (Futuro) para Dashboard
```http
GET /api/v1/metrics/price-trend?listing_id=42&from=2025-11-01&to=2025-11-30
Response: {
  "listing_id":42,
  "currency":"USD",
  "points":[{"date":"2025-11-01","avg":120.5},{"date":"2025-11-02","avg":118.0}]
}
```

## 11. Accesibilidad Básica
- Descripciones aria en componentes interactivos.  
- Evitar solo color para transmitir estado (usar íconos/etiquetas).  

## 12. Roadmap UI
| Fase | Entrega |
|------|---------|
| S1 | Refactor componentes Streamlit reutilizables |
| S2 | API REST para lectura básica |
| S3 | Migración parcial a frontend React (Dashboard + Eventos) |
| S4 | Integración tiempo real (websockets) |

---
Fin del documento de UI V3.
