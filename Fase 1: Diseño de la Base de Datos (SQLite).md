### Fase 1: Diseño de la Base de Datos (Versión Final)

Este documento define la estructura de la base de datos **SQLite** que servirá como el único almacén de datos para la aplicación Price-Monitor.

Se adopta un **diseño normalizado de 3 tablas** para garantizar la máxima flexibilidad y escalabilidad, permitiendo que un solo "Establecimiento" (el concepto) tenga múltiples URLs de monitoreo (las plataformas).

-----

### Tabla 1: `Establecimientos`

**Propósito:** Almacena el "concepto" o la "entidad" que el usuario desea monitorear. Es la carpeta principal.

```sql
CREATE TABLE Establecimientos (
    id_establecimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_personalizado TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Columnas:

  * `id_establecimiento`: (Clave Primaria / PK) Un ID numérico único que identifica la propiedad (Ej: 1 = "Cabaña Sol").
  * `nombre_personalizado`: El nombre amigable que el usuario le da a la propiedad (Ej: "Cabaña Sol", "Depto Centro").
  * `fecha_creacion`: Sello de tiempo de cuándo se registró la propiedad.

-----

### Tabla 2: `Plataformas_URL`

**Propósito:** El "conector". Vincula un `Establecimiento` (Tabla 1) con una o más URLs de scraping específicas. Aquí es donde se define el trabajo a realizar.

```sql
CREATE TABLE Plataformas_URL (
    id_plataforma_url INTEGER PRIMARY KEY AUTOINCREMENT,
    id_establecimiento INTEGER NOT NULL,
    
    plataforma TEXT NOT NULL, -- Ej: 'Booking', 'Airbnb', 'Vrbo'
    url TEXT NOT NULL UNIQUE, -- La URL exacta que el scraper debe visitar
    
    esta_activa BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (id_establecimiento) 
        REFERENCES Establecimientos(id_establecimiento) 
        ON DELETE CASCADE
);
```

#### Columnas:

  * `id_plataforma_url`: (Clave Primaria / PK) Un ID numérico único para *cada URL* (Ej: 101).
  * `id_establecimiento`: (Clave Foránea / FK) El ID de la Tabla 1 al que pertenece esta URL (Ej: 1, vinculando a "Cabaña Sol").
  * `plataforma`: Un nombre de texto para identificar la plataforma (Ej: "Booking").
  * `url`: La URL completa y única del anuncio a scrapear.
  * `esta_activa`: Un interruptor (Verdadero/Falso). Permite al usuario "pausar" el monitoreo de esta URL sin tener que borrar el registro.

-----

### Tabla 3: `Precios`

**Propósito:** El corazón de la aplicación. Almacena cada punto de dato (precio, ocupación, etc.) recolectado para una URL específica en una fecha específica.

```sql
CREATE TABLE Precios (
    id_plataforma_url INTEGER NOT NULL, -- La URL específica que generó este dato
    fecha_noche DATE NOT NULL, -- La noche específica que se está cotizando
    
    -- Datos del Scrape --
    precio_base REAL, -- El precio base (o 0 si no disponible)
    esta_ocupado BOOLEAN DEFAULT FALSE, -- (Q19: True si precio_base es 0)
    
    -- Detalles (Q7) --
    incluye_limpieza_base TEXT DEFAULT 'No Informa', -- 'Sí', 'No', 'No Informa'
    incluye_impuestos_base TEXT DEFAULT 'No Informa', -- 'Sí', 'No', 'No Informa'
    ofrece_desayuno TEXT DEFAULT 'No Informa', -- 'Sí', 'No', 'No Informa'

    -- Metadatos de Control --
    fecha_scrape TIMESTAMP NOT NULL, -- Cuándo se obtuvo este dato (para lógica de 48h)
    noches_encontradas INTEGER, -- 1, 2 o 3 (la búsqueda que tuvo éxito)
    error_log TEXT, -- Para registrar un aviso de bloqueo (Q9)

    -- Claves --
    FOREIGN KEY (id_plataforma_url) 
        REFERENCES Plataformas_URL(id_plataforma_url) 
        ON DELETE CASCADE,
    
    -- Clave Primaria Compuesta --
    PRIMARY KEY (id_plataforma_url, fecha_noche)
);
```

#### Columnas:

  * `id_plataforma_url`: (Clave Foránea / FK) El ID de la Tabla 2 que generó este dato (Ej: 101).
  * `fecha_noche`: La fecha de la estadía (Ej: '2025-12-25').
  * `precio_base`: El precio base por noche encontrado.
  * `esta_ocupado`: (Q19) Se setea en `TRUE` si `precio_base` es `0`.
  * `incluye_...`: (Q7) Detalles adicionales extraídos por el scraper.
  * `fecha_scrape`: (Crucial para Q12) Sello de tiempo de *cuándo se ejecutó* el scrape.
  * `noches_encontradas`: Registra qué lógica de búsqueda (1, 2 o 3 noches) tuvo éxito.
  * `error_log`: Almacena mensajes de error (Ej: "CAPTCHA detectado").
  * `PRIMARY KEY (id_plataforma_url, fecha_noche)`: Esto es **fundamental**. Asegura que solo exista **un único registro de precio** para una URL específica en una noche específica.

-----

### Lógica de Actualización (UPSERT)

Para cumplir con la **Q12** (actualizar precios futuros si tienen \> 48h), la aplicación **no** usará un `INSERT` simple. Usará una lógica `UPSERT` de 3 pasos:

1.  **Leer (Q15):** Antes de scrapear, la app consulta la tabla `Precios` para el `id_plataforma_url` y el rango de fechas solicitado.

2.  **Filtrar (Lógica 48h):** El script crea su "lista de tareas" *solo* para las noches que:

      * No existen en la base de datos.
      * O, existen, pero `(fecha_actual - fecha_scrape) > 48 horas`.

3.  **Escribir (UPSERT):** Por cada precio nuevo encontrado, ejecutará una única consulta `INSERT ... ON CONFLICT` que actualiza el registro si ya existe:

    ```sql
    INSERT INTO Precios (
        id_plataforma_url, 
        fecha_noche, 
        precio_base, 
        esta_ocupado, 
        fecha_scrape, 
        ...
    )
    VALUES (?, ?, ?, ?, ?, ...)
    ON CONFLICT(id_plataforma_url, fecha_noche) DO UPDATE SET
        precio_base = excluded.precio_base,
        esta_ocupado = excluded.esta_ocupado,
        fecha_scrape = excluded.fecha_scrape,
        incluye_limpieza_base = excluded.incluye_limpieza_base,
        incluye_impuestos_base = excluded.incluye_impuestos_base,
        ofrece_desayuno = excluded.ofrece_desayuno,
        noches_encontradas = excluded.noches_encontradas,
        error_log = excluded.error_log
    ;
    ```

-----

### Mejoras de Rendimiento: Índices

Para garantizar consultas rápidas (especialmente con filtros por fecha), se crearán los siguientes índices:

```sql
-- Índice para búsquedas por fecha de noche (usado en Dashboard y filtros)
CREATE INDEX idx_precios_fecha_noche ON Precios(fecha_noche);

-- Índice para lógica de 48h (consultas por fecha_scrape)
CREATE INDEX idx_precios_fecha_scrape ON Precios(fecha_scrape);

-- Índice para búsquedas por establecimiento (JOIN frecuente)
CREATE INDEX idx_plataformas_establecimiento ON Plataformas_URL(id_establecimiento);

-- Índice compuesto para consultas combinadas (establecimiento + fecha)
CREATE INDEX idx_precios_url_fecha ON Precios(id_plataforma_url, fecha_noche);
```

-----

### Mejoras de Validación: Constraints

Para prevenir datos inconsistentes y errores de typo:

```sql
-- Actualización de la tabla Plataformas_URL con constraint de validación
CREATE TABLE Plataformas_URL (
    id_plataforma_url INTEGER PRIMARY KEY AUTOINCREMENT,
    id_establecimiento INTEGER NOT NULL,
    
    plataforma TEXT NOT NULL CHECK(plataforma IN ('Booking', 'Airbnb', 'Vrbo')), 
    url TEXT NOT NULL UNIQUE,
    
    esta_activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_establecimiento) 
        REFERENCES Establecimientos(id_establecimiento) 
        ON DELETE CASCADE
);
```

**Nota:** El constraint `CHECK(plataforma IN (...))` asegura que solo se puedan registrar plataformas con robots implementados.
````
    ```