-- ============================================================
-- Price-Monitor Database Schema (V3 MINIMAL)
-- SQLite 3.x
-- Versión: 3.0.0 (Skeleton)
-- Fecha: 2025-11-08
-- ============================================================

-- ==========================
-- TABLA CENTRAL: Establecimientos
-- ==========================
-- Mantener la entidad raíz única para reconstruir el resto del dominio.

CREATE TABLE IF NOT EXISTS Establecimientos (
    id_establecimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_personalizado TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- NOTAS DE MIGRACIÓN
-- ============================================================
-- Se eliminaron todas las tablas derivadas (Plataformas_URL, Precios) y vistas.
-- El nuevo modelo usará Observaciones y Normalizaciones en siguientes iteraciones.
-- Este schema mínimo permite conservar la base funcional de la aplicación.

/* Datos de prueba mínimos (comentados) */
/*
INSERT INTO Establecimientos (nombre_personalizado) VALUES ('Ejemplo Base');
*/
