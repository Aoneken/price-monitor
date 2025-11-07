### Documento Introductorio: App Price-Monitor (Versión Final)

#### 1. Resumen Ejecutivo

**App Price-Monitor** es una herramienta de inteligencia de precios (PI) diseñada como una aplicación web interna. Construida sobre **Streamlit** y **Python**, su arquitectura es fundamentalmente **modular** y **escalable**.

La aplicación permite a los usuarios gestionar un portafolio de establecimientos, cada uno con múltiples URLs de plataformas (Booking, Airbnb, etc.). Ejecuta un scraper "prudente" para recolectar precios por noche, aplicando una lógica de negocio para optimizar las búsquedas (regla de 48h) e inferir la ocupación. Los datos se centralizan en una base de datos SQLite, listos para ser visualizados en un dashboard de inteligencia o exportados.

#### 2. Objetivo del Proyecto

El objetivo principal es construir una base de datos histórica, robusta y consultable sobre precios y ocupación. Esta base de datos permitirá al usuario:

1.  Identificar patrones de precios y estacionalidad.
2.  Analizar la ocupación (inferida) del mercado o de competidores.
3.  Visualizar la evolución de tarifas a través de un dashboard interactivo.
4.  Servir como fundamento para el futuro módulo de "Análisis" (Pestaña 5), **un objetivo facilitado por el diseño modular de la aplicación**.

#### 3. Alcance y Arquitectura (MVP)

El alcance del MVP se define por las siguientes decisiones de arquitectura, tomadas durante las fases de diseño:

* **Plataforma General:**
    * **Interfaz (Fase 3):** **Streamlit**, priorizando la funcionalidad en tiempo real y la rapidez de desarrollo.
    * **Backend:** **Python**.

* **Arquitectura de Base de Datos (Fase 1):**
    * **Sistema:** **SQLite** (para portabilidad y simplicidad en MVP).
    * **Diseño:** Modelo **Normalizado de 3 Tablas** (`Establecimientos`, `Plataformas_URL`, `Precios`). 
    * **Optimizaciones:**
        - Índices en columnas de búsqueda frecuente (fecha_noche, fecha_scrape)
        - Constraint CHECK para validar plataformas soportadas
        - Clave primaria compuesta para garantizar unicidad (URL + Fecha)
    * Este diseño garantiza la escalabilidad, permitiendo que un establecimiento sea monitoreado en un número ilimitado de plataformas o URLs simultáneamente.
    * **Nota:** Para >5 usuarios simultáneos, migrar a PostgreSQL.

* **Arquitectura de Scraper (Fase 2):**
    * **Motor:** **Playwright** con playwright-stealth para control de navegador *headless* y evasión de bloqueos.
    * **Diseño:** **Patrón "Strategy + Factory"**. La aplicación utiliza:
        - Un "Orquestador" central que gestiona tareas y delega el trabajo
        - Un "Factory" que instancia robots dinámicamente según la plataforma
        - "Robots" modulares e intercambiables (ej: `BookingRobot`, `AirbnbRobot`)
        - Selectores CSS externalizados en JSON para fácil mantenimiento
        - Sistema de retry con exponential backoff para fallos transitorios
    * Esto permite añadir o modificar plataformas sin afectar el núcleo de la aplicación.

* **Lógica de Negocio Clave:**
    1.  **Búsqueda (3->2->1):** Lógica de fallback para encontrar disponibilidad (Q2).
    2.  **Frescura (48h):** El Orquestador no buscará un precio si ya existe un dato con menos de 48 horas de antigüedad (Q12, Q15).
    3.  **Ocupación:** Si una búsqueda (3, 2 y 1 noche) falla, se asume `Precio = 0` y `Esta_Ocupado = TRUE` (Q19).

#### 4. Estructura de la Aplicación (Pestañas)

La interfaz de Streamlit (Fase 3) se organizará en 5 pestañas para separar claramente las funcionalidades:

1.  **`Establecimientos`**: (Fase 1) CRUD para gestionar el portafolio de propiedades y sus URLs asociadas.
2.  **`Scraping`**: (Fase 2) El panel de control para iniciar el `principal_orchestrator` y ver la tabla de resultados temporales "en vivo".
3.  **`Base de Datos`**: (Fase 1) Un visor completo de la tabla `Precios` con filtros y capacidad de exportación.
4.  **`Dashboard`**: (Fase 3) El centro de inteligencia visual. (MVP: Gráfico de líneas de precio/ocupación).
5.  **`Análisis`**: (Futuro) Un *placeholder* para el módulo de "Cliente vs. Competidor" (Q16, Q20).