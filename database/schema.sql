-- ============================================================
-- Price-Monitor Database Schema
-- SQLite 3.x
-- Versión: 1.0
-- Fecha: 2025-11-06
-- ============================================================

-- ==========================
-- TABLA 1: Establecimientos
-- ==========================
-- Propósito: Almacena el "concepto" o la "entidad" que el usuario desea monitorear

CREATE TABLE IF NOT EXISTS Establecimientos (
    id_establecimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_personalizado TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================
-- TABLA 2: Plataformas_URL
-- ==========================
-- Propósito: Vincula un Establecimiento con una o más URLs de scraping específicas

CREATE TABLE IF NOT EXISTS Plataformas_URL (
    id_plataforma_url INTEGER PRIMARY KEY AUTOINCREMENT,
    id_establecimiento INTEGER NOT NULL,
    
    -- Nombre de la plataforma (debe coincidir con un robot implementado)
    plataforma TEXT NOT NULL CHECK(plataforma IN ('Booking', 'Airbnb', 'Vrbo')),
    
    -- La URL exacta que el scraper debe visitar
    url TEXT NOT NULL UNIQUE,
    
    -- Interruptor para pausar/reactivar el monitoreo
    esta_activa BOOLEAN DEFAULT TRUE,
    
    -- Auditoría: cuándo se agregó esta URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Clave foránea con eliminación en cascada
    FOREIGN KEY (id_establecimiento) 
        REFERENCES Establecimientos(id_establecimiento) 
        ON DELETE CASCADE
);

-- ==========================
-- TABLA 3: Precios
-- ==========================
-- Propósito: Almacena cada punto de dato recolectado para una URL en una fecha específica

CREATE TABLE IF NOT EXISTS Precios (
    -- Identificador de la URL que generó este dato
    id_plataforma_url INTEGER NOT NULL,
    
    -- La noche específica que se está cotizando (YYYY-MM-DD)
    fecha_noche DATE NOT NULL,
    
    -- === Datos del Scrape ===
    precio_base REAL,                              -- Precio base por noche (0 si no disponible)
    esta_ocupado BOOLEAN DEFAULT FALSE,            -- TRUE si precio_base es 0
    
    -- === Detalles Adicionales ===
    incluye_limpieza_base TEXT DEFAULT 'No Informa',   -- 'Sí', 'No', 'No Informa'
    incluye_impuestos_base TEXT DEFAULT 'No Informa',  -- 'Sí', 'No', 'No Informa'
    ofrece_desayuno TEXT DEFAULT 'No Informa',         -- 'Sí', 'No', 'No Informa'

    -- === Metadatos de Control ===
    fecha_scrape TIMESTAMP NOT NULL,               -- Cuándo se obtuvo este dato (para lógica de 48h)
    noches_encontradas INTEGER,                    -- 1, 2 o 3 (la búsqueda que tuvo éxito)
    error_log TEXT,                                -- Mensajes de error (CAPTCHA, bloqueos, etc.)

    -- === Claves ===
    FOREIGN KEY (id_plataforma_url) 
        REFERENCES Plataformas_URL(id_plataforma_url) 
        ON DELETE CASCADE,
    
    -- Clave Primaria Compuesta: garantiza un único registro por URL+Fecha
    PRIMARY KEY (id_plataforma_url, fecha_noche)
);

-- ============================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE RENDIMIENTO
-- ============================================================

-- Índice para búsquedas por fecha de noche (Dashboard, filtros)
CREATE INDEX IF NOT EXISTS idx_precios_fecha_noche 
ON Precios(fecha_noche);

-- Índice para lógica de 48h (consultas por fecha_scrape)
CREATE INDEX IF NOT EXISTS idx_precios_fecha_scrape 
ON Precios(fecha_scrape);

-- Índice para búsquedas por establecimiento (JOIN frecuente)
CREATE INDEX IF NOT EXISTS idx_plataformas_establecimiento 
ON Plataformas_URL(id_establecimiento);

-- Índice compuesto para consultas combinadas (establecimiento + fecha)
CREATE INDEX IF NOT EXISTS idx_precios_url_fecha 
ON Precios(id_plataforma_url, fecha_noche);

-- Índice para filtrar URLs activas
CREATE INDEX IF NOT EXISTS idx_plataformas_activa 
ON Plataformas_URL(esta_activa);

-- ============================================================
-- VISTAS ÚTILES (Opcional - Para simplificar consultas)
-- ============================================================

-- Vista que combina las 3 tablas para consultas fáciles
CREATE VIEW IF NOT EXISTS vista_precios_completa AS
SELECT 
    e.id_establecimiento,
    e.nombre_personalizado AS establecimiento,
    p.id_plataforma_url,
    p.plataforma,
    p.url,
    p.esta_activa,
    pr.fecha_noche,
    pr.precio_base,
    pr.esta_ocupado,
    pr.incluye_limpieza_base,
    pr.incluye_impuestos_base,
    pr.ofrece_desayuno,
    pr.fecha_scrape,
    pr.noches_encontradas,
    pr.error_log
FROM Precios pr
JOIN Plataformas_URL p ON pr.id_plataforma_url = p.id_plataforma_url
JOIN Establecimientos e ON p.id_establecimiento = e.id_establecimiento;

-- ============================================================
-- DATOS DE PRUEBA (Opcional - Para desarrollo)
-- ============================================================

-- Descomentar para insertar datos de ejemplo:
/*
INSERT INTO Establecimientos (nombre_personalizado) VALUES 
    ('Cabaña Sol'),
    ('Departamento Centro');

INSERT INTO Plataformas_URL (id_establecimiento, plataforma, url) VALUES 
    (1, 'Booking', 'https://www.booking.com/hotel/ejemplo1.html'),
    (1, 'Airbnb', 'https://www.airbnb.com/rooms/12345678'),
    (2, 'Booking', 'https://www.booking.com/hotel/ejemplo2.html');
*/
