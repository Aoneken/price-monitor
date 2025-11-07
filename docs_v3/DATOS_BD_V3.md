# DATOS & BASE DE DATOS V3

## 1. Objetivos del Rediseño
- Separar observaciones brutas de normalizaciones.  
- Facilitar migración a Postgres y potencial uso de Timescale para series temporales.  
- Elevar trazabilidad y calidad.  

## 2. Esquema Propuesto (Postgres)
```sql
-- Tabla principal estable (dominio)
CREATE TABLE establecimientos (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  zona TEXT,
  tags TEXT[],
  fecha_creacion TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE plataformas (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL UNIQUE, -- 'Booking', 'Airbnb', etc.
  tipo TEXT NOT NULL DEFAULT 'scrape', -- scrape/api/manual
  activo BOOLEAN DEFAULT TRUE,
  url_base TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE listings (
  id SERIAL PRIMARY KEY,
  establecimiento_id INT REFERENCES establecimientos(id) ON DELETE CASCADE,
  plataforma_id INT REFERENCES plataformas(id) ON DELETE RESTRICT,
  external_ref TEXT, -- ID externo / slug
  url TEXT,
  activa BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(plataforma_id, external_ref)
);

CREATE TABLE selector_versions (
  id SERIAL PRIMARY KEY,
  plataforma_id INT REFERENCES plataformas(id),
  version_semver TEXT NOT NULL,
  checksum TEXT NOT NULL,
  published_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(plataforma_id, version_semver)
);

CREATE TABLE robot_executions (
  id SERIAL PRIMARY KEY,
  listing_id INT REFERENCES listings(id),
  selector_version_id INT REFERENCES selector_versions(id),
  robot_name TEXT NOT NULL,
  robot_version TEXT NOT NULL,
  inicio TIMESTAMPTZ NOT NULL,
  fin TIMESTAMPTZ NOT NULL,
  duracion_ms INT,
  reintentos INT,
  resultado_estado TEXT, -- success, blocked, partial
  error_code TEXT,
  bloqueo_detectado BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE price_observations (
  id BIGSERIAL PRIMARY KEY,
  listing_id INT REFERENCES listings(id),
  fecha_noche DATE NOT NULL,
  fecha_ingesta TIMESTAMPTZ NOT NULL,
  noches_consultadas INT CHECK (noches_consultadas IN (1,2,3)),
  precio_total_original NUMERIC(12,2) CHECK (precio_total_original >= 0),
  moneda_original CHAR(3) NOT NULL,
  impuestos_flag BOOLEAN,
  desayuno_flag BOOLEAN,
  fuente_tipo TEXT NOT NULL, -- scrape/api/manual
  raw_hash TEXT,
  robot_version TEXT,
  calidad_score NUMERIC(4,3) CHECK (calidad_score BETWEEN 0 AND 1),
  UNIQUE(listing_id, fecha_noche, robot_version, fecha_ingesta)
);

CREATE TABLE price_normalized (
  id BIGSERIAL PRIMARY KEY,
  price_observation_id BIGINT REFERENCES price_observations(id) ON DELETE CASCADE,
  moneda_base CHAR(3) NOT NULL DEFAULT 'USD',
  fx_rate NUMERIC(12,6) CHECK (fx_rate > 0),
  precio_por_noche NUMERIC(12,2) CHECK (precio_por_noche >= 0),
  normalization_timestamp TIMESTAMPTZ DEFAULT NOW(),
  metodo TEXT DEFAULT 'fx_latest'
);

CREATE TABLE availability_observations (
  id BIGSERIAL PRIMARY KEY,
  listing_id INT REFERENCES listings(id),
  fecha_noche DATE NOT NULL,
  fecha_ingesta TIMESTAMPTZ NOT NULL,
  estado TEXT CHECK (estado IN ('disponible','ocupado','unknown')),
  metodo_inferencia TEXT,
  UNIQUE(listing_id, fecha_noche, fecha_ingesta)
);

CREATE TABLE fx_rates (
  id BIGSERIAL PRIMARY KEY,
  fecha DATE NOT NULL,
  moneda CHAR(3) NOT NULL,
  rate_vs_base NUMERIC(12,6) NOT NULL CHECK (rate_vs_base > 0),
  source TEXT,
  UNIQUE(fecha, moneda)
);

CREATE TABLE event_log (
  id BIGSERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  INDEX (event_type),
  INDEX ((payload->>'listing_id'))
);
```

## 3. Índices Clave
```sql
CREATE INDEX idx_price_obs_listing_fecha ON price_observations(listing_id, fecha_noche);
CREATE INDEX idx_price_obs_ingesta ON price_observations(fecha_ingesta);
CREATE INDEX idx_price_norm_observation ON price_normalized(price_observation_id);
CREATE INDEX idx_availability_listing_fecha ON availability_observations(listing_id, fecha_noche);
CREATE INDEX idx_robot_exec_listing ON robot_executions(listing_id);
CREATE INDEX idx_event_log_type ON event_log(event_type);
```

## 4. Estrategia de Migración desde SQLite
1. Exportar `Establecimientos` y `Plataformas_URL` actuales.  
2. Mapear `Plataformas_URL` → `listings` (generar `plataforma_id`).  
3. Transformar `Precios` → `price_observations` (precio_total_original = precio_base * noches_encontradas).  
4. Generar `price_normalized` inicial (fx_rate = 1 para USD, placeholder).  
5. Inferir Availability desde `esta_ocupado`.  
6. Etiquetar robot_version = 'legacy-v1.x'.  

## 5. Vistas Materializadas (Performance)
```sql
CREATE MATERIALIZED VIEW mv_daily_price AS
SELECT listing_id, fecha_noche,
       AVG(precio_por_noche) AS avg_price,
       COUNT(*) AS samples
FROM price_normalized pn
JOIN price_observations po ON pn.price_observation_id = po.id
GROUP BY listing_id, fecha_noche;
```
Refresco: cada 30 min o tras lote de ingesta.

## 6. Estrategia de Particionado (Futuro Postgres)
- `price_observations` partición por rango mensual (fecha_ingesta).  
- `availability_observations` partición diaria si volumen crece.  

## 7. Integridad Referencial y Limpieza
- Purga: mover registros > retención a tabla archivada o almacenamiento S3 parquet.  
- No cascada destructiva sobre `price_observations` salvo borrado listing explícito.  

## 8. Validación de Calidad
Job nocturno: recalcula percentiles por plataforma y marca anomalías (inserta en `event_log` tipo `PriceAnomalyDetected`).  

## 9. Ejemplos de Consultas
Precio promedio por zona y plataforma última semana:
```sql
SELECT e.zona, p.nombre AS plataforma, AVG(pn.precio_por_noche) AS avg_price
FROM price_normalized pn
JOIN price_observations po ON pn.price_observation_id = po.id
JOIN listings l ON po.listing_id = l.id
JOIN establecimientos e ON l.establecimiento_id = e.id
JOIN plataformas p ON l.plataforma_id = p.id
WHERE po.fecha_noche BETWEEN CURRENT_DATE - INTERVAL '7 days' AND CURRENT_DATE
GROUP BY e.zona, p.nombre;
```

## 10. Plan de Evolución
- Añadir tabla `recommendations` posterior a ML.  
- Introducir `quality_incidents` para capturar problemas sistemáticos.  

---
Fin del documento de datos y BD V3.
