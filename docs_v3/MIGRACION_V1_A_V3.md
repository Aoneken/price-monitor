# MIGRACIÓN DE V1.x A V3

## 1. Objetivo
Plan controlado para pasar del esquema y arquitectura actuales al nuevo modelo sin pérdida de datos críticos.

## 2. Inventario Actual (v1.x)
- Tablas: Establecimientos, Plataformas_URL, Precios.  
- Lógica: Orquestador sincrónico + robots directos.  
- Tests: Básicos BD, E2E, scraping parcial.  

## 3. Gap Principal
| Área | V1 | V3 |
|------|----|----|
| Datos | Mezcla precio y disponibilidad | Separación + normalización |
| Arquitectura | Monolítica, sin eventos | Event-driven modular |
| Scraping | Foco DOM selectores | Multi-estrategia + validación |
| Observabilidad | Logs planos | Logs estructurados + métricas |

## 4. Estrategia de Migración
Fases:  
1. Congelar versión v1.3.1 (tag).  
2. Exportar datos SQLite → CSV intermedios.  
3. Crear nuevo esquema en Postgres.  
4. Ejecutar script `migrate_v1_to_v3.py`:
   - Mapear Establecimientos.
   - Crear plataformas (Booking, Airbnb, Expedia).  
   - Generar listings desde Plataformas_URL.  
   - Para cada fila en Precios: crear PriceObservation (precio_total_original = precio_base * (noches_encontradas or 1)).  
   - Derivar AvailabilityObservation desde esta_ocupado.  
   - Crear PriceNormalized (fx_rate=1 USD provisional).  
5. Validar conteos y muestra aleatoria (10%).  
6. Activar pipeline nuevo sólo para subset (canary).  
7. Comparar precios entre legacy y nuevo (delta < tolerancia).  
8. Switch total.  

## 5. Script de Migración (Pseudocódigo)
```python
for est in sqlite.Establecimientos: postgres.insert_establecimiento(est)
for url in sqlite.Plataformas_URL:
    plataforma_id = get_or_create_plataforma(url.plataforma)
    listing_id = insert_listing(est_id=url.id_establecimiento, plataforma_id, external_ref=derive_ref(url.url), url=url.url)
for precio in sqlite.Precios:
    listing_id = map_url_to_listing(precio.id_plataforma_url)
    obs_id = insert_price_observation(listing_id, fecha_noche, fecha_scrape, noches_encontradas, precio_base*noches_encontradas, 'USD')
    norm_id = insert_price_normalized(obs_id, precio_base, fx_rate=1)
    avail_id = insert_availability(listing_id, fecha_noche, fecha_scrape, estado = 'ocupado' if precio_base==0 else 'disponible')
```

## 6. Validación Post Migración
| Check | Método |
|-------|--------|
| Conteo establecimientos | Igual al original |
| Conteo listings | Igual a Plataformas_URL |
| Conteo price_observations | Igual a Precios |
| Muestra aleatoria | Manual diff precios |
| Ocupación | Proporción coincide |

## 7. Rollback
Si falla canary: revertir a backup SQLite + pausar ingestión v3; analizar incidentes.  

## 8. Riesgos
- Precio total vs precio por noche mal interpretado.  
- URLs no parseables para external_ref.  

## 9. Herramientas
- Script verificación: compara agregados por día antes/después.  
- Reporte `migration_report.json` con totales y hashes.  

---
Fin del documento migración V3.
