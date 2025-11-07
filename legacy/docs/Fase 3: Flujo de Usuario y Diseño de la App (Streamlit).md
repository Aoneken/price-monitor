### Fase 3: Flujo de Usuario y Diseño de la App (Streamlit)

Este documento detalla la funcionalidad y el diseño de la interfaz de la aplicación Streamlit, dividida en las 5 pestañas que definimos (Q16).



---

#### 1. Pestaña 1: `Establecimientos` (CRUD)

**Objetivo:** Gestionar el portafolio de propiedades a monitorear (CRUD - Crear, Leer, Editar, Eliminar). Esta pestaña interactúa con las tablas `Establecimientos` y `Plataformas_URL` de la BBDD (Fase 1).

**Diseño de la Interfaz:**
La pestaña tendrá un diseño "Maestro-Detalle".

**Sección 1: Maestro (Gestionar Establecimientos)**
* **Formulario "Añadir Nuevo Establecimiento":**
    * Input de Texto: `Nombre Personalizado` (Ej: "Cabaña Sol").
    * Botón: `[Añadir Establecimiento]`
    * *Acción SQL:* `INSERT INTO Establecimientos (nombre_personalizado) VALUES (?)`
* **Selector "Gestionar Establecimiento Existente":**
    * Selectbox (Menú desplegable): "Seleccionar Establecimiento" (se carga con una consulta `SELECT * FROM Establecimientos`).
    * Botón: `[Eliminar Establecimiento Seleccionado]` (¡con confirmación!).
    * *Acción SQL:* `DELETE FROM Establecimientos WHERE id_establecimiento = ?`

**Sección 2: Detalle (Gestionar URLs de la Plataforma)**
*Esta sección solo aparece después de seleccionar un establecimiento de la lista de arriba.*
* **Tabla "URLs Registradas para [Nombre del Establecimiento]":**
    * Muestra una tabla de todas las URLs asociadas a ese `id_establecimiento`.
    * Columnas: `ID_URL`, `Plataforma`, `URL`, `Activa`, `[Acciones]`
    * `[Acciones]` contiene:
        * Un *toggle* (interruptor) para cambiar `esta_activa` (True/False). (Q11)
        * Un botón `[Borrar]` para eliminar esa URL.
* **Formulario "Añadir Nueva URL a [Nombre del Establecimiento]":**
    * Input de Texto: `Plataforma` (Ej: "Booking", "Airbnb"). *Importante: Este nombre debe coincidir con el nombre de un "Robot" de la Fase 2.*
    * Input de Texto: `URL Completa`.
    * Botón: `[Guardar URL]`
    * *Acción SQL:* `INSERT INTO Plataformas_URL (id_establecimiento, plataforma, url) VALUES (?, ?, ?)`

---

#### 2. Pestaña 2: `Scraping` (El Iniciador)

**Objetivo:** Ejecutar el proceso de scraping (definido en Fase 2) y mostrar el progreso "en vivo" (Q13).

**Diseño de la Interfaz:**
**Sección 1: Configuración de la Tarea**
* **Selectbox (Menú desplegable): "Seleccionar Establecimiento":**
    * Se carga con `SELECT * FROM Establecimientos`.
    * El usuario elige qué propiedad quiere scrapear.
* **Selector de Rango de Fechas:**
    * Input de Fecha: `Fecha de Inicio`.
    * Input de Fecha: `Fecha de Fin`.
* **Botón de Ejecución:**
    * Botón: `[ INICIAR MONITOREO ]`
    * *Acción:* Al hacer clic, se bloquea el formulario y se llama a la función `principal_orchestrator(id, inicio, fin)` de la Fase 2.

**Sección 2: Panel de Resultados (En Vivo)**
*Esta sección está vacía hasta que se hace clic en el botón.*
* **Barra de Progreso (Requisito original):**
    * Un `st.progress(0)` que se actualiza.
    * `progreso = (fechas_procesadas / fechas_totales_a_buscar)`.
* **Tabla de Log/Temporal (Q13):**
    * Un contenedor (`st.container` o `st.dataframe`) que se actualiza en tiempo real.
    * Cada vez que el Orquestador (Fase 2) completa una fecha, añade una fila a esta vista temporal:
    * *Ejemplo de Fila:* `[Plataforma: Booking] [Fecha: 2025-12-01] [Noches: 3] [Precio: $120.00] [Estado: Guardado]`
    * *Ejemplo de Error:* `[Plataforma: Airbnb] [Fecha: 2025-12-02] [Estado: ¡BLOQUEO DETECTADO!]`

---

#### 3. Pestaña 3: `Base de Datos` (El Visor)

**Objetivo:** Permitir al usuario ver y filtrar *toda* la base de datos `Precios` (Q16). Sirve para validación de datos y exportación.

**Diseño de la Interfaz:**
**Sección 1: Filtros de Búsqueda**
* **Multiselect: "Establecimientos":** (Elige uno o más).
* **Multiselect: "Plataformas":** (Elige una o más).
* **Date Range: "Rango de Fechas (Noche)":**
* **Date Range: "Rango de Fechas (Scrape)":** (Para ver datos "frescos").
* **Checkbox: "Mostrar solo Ocupados (`Precio=0`)":**
* **Botón:** `[Buscar en BBDD]`

**Sección 2: Tabla de Resultados**
* Un `st.dataframe` que muestra los resultados de la consulta SQL (un `JOIN` de las 3 tablas).
* **Botón de Descarga:**
    * `st.download_button("Exportar a CSV", data=...)`

---

#### 4. Pestaña 4: `Dashboard` (La Inteligencia)

**Objetivo:** Visualizar los datos de forma agregada para obtener *insights* (Q17).

**Diseño de la Interfaz:**
**Sección 1: Filtros del Dashboard**
* **Selectbox: "Seleccionar Establecimiento":** (Solo permite *uno* para que el gráfico sea claro).
* **Date Range: "Periodo de Análisis":**
* **Radio Button: "Métrica Principal" (Q17):**
    * Opción 1: `Precio`
    * Opción 2: `Ocupación`
* **Checkbox: "Comparar Plataformas":** (Si se marca, el gráfico muestra una línea por plataforma; si no, muestra el promedio de todas - Q17).

**Sección 2: Visualización**
* **Métricas Clave (KPIs):**
    * `st.metric("Precio Promedio (Periodo)", "$150.50")`
    * `st.metric("Tasa de Ocupación (Periodo)", "75%")`
    * `st.metric("Dato más reciente", "Hace 3 horas")`
* **Gráfico de Líneas (Q17):**
    * Un `st.line_chart` que muestra la métrica seleccionada a lo largo del tiempo.
    * **Eje X:** `fecha_noche`
    * **Eje Y:** `Precio` o `Ocupación` (basado en el Radio Button).
    * **Lógica de Datos:** El código debe consultar la BBDD, filtrar por el establecimiento y las fechas, y luego `GROUP BY fecha_noche` para calcular `AVG(precio_base)` (si `precio > 0`) o `SUM(esta_ocupado)`.



---

#### 5. Pestaña 5: `Análisis` (Placeholder)

**Objetivo:** Dejar el espacio listo para la futura funcionalidad de "Cliente vs. Competidor" (Q16, Q20).

**Diseño de la Interfaz:**
* `st.title("Módulo de Análisis (Próximamente)")`
* `st.info("Esta sección permitirá seleccionar un establecimiento 'Cliente' y compararlo contra un grupo de 'Competidores' para generar recomendaciones de precios.")`
* `(Contenido en blanco)`