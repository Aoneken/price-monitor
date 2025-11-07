### Fase 2: Lógica de Scraping y Orquestación (Versión Final)

Este documento define la arquitectura de software y el pseudocódigo del "cerebro" de la aplicación: el orquestador que gestiona las tareas y los "robots" (scrapers) que extraen los datos.

La arquitectura se basa en **Strategy Pattern + Factory Pattern**: 
- Un "Orquestador" central que no sabe *cómo* scrapear, sino que delega el trabajo a "Robots" modulares.
- Un "Factory" que instancia dinámicamente el robot correcto según la plataforma.
- "Robots" específicos para cada plataforma (Booking, Airbnb, etc.) con selectores externalizados.

**Tecnologías:** Python 3.11+, Playwright (con playwright-stealth para anti-detección).

-----

#### 1\. El Orquestador (Alto Nivel)

Esta es la función principal que se ejecuta desde la Pestaña `Scraping`. Su trabajo es gestionar las colas de trabajo, la lógica de 48h y delegar la ejecución al robot correcto.

```python
# --- PSEUDOCÓDIGO DE ORQUESTACIÓN ---

FUNCION principal_orchestrator(id_establecimiento_elegido, fecha_inicio, fecha_fin):
    
    # 1. OBTENER TAREAS
    # Busca en la BBDD todas las URLs activas para el establecimiento elegido.
    lista_urls_activas = CONSULTAR_SQL(
        "SELECT id_plataforma_url, plataforma, url 
         FROM Plataformas_URL 
         WHERE id_establecimiento = ? AND esta_activa = TRUE",
        id_establecimiento_elegido
    )

    # 2. INICIAR NAVEGADOR
    # (Q14) Inicia el navegador una sola vez para ser eficiente.
    # Se configura para parecer humano (User-Agent, etc.)
    navegador = INICIAR_NAVEGADOR_PLAYWRIGHT()

    # 3. BUCLE POR CADA URL (Booking, Airbnb, etc.)
    PARA CADA url_info EN lista_urls_activas:
        
        # 4. APLICAR LÓGICA DE 48 HORAS (Q15)
        # Obtenemos la lista *optimizada* de fechas que SÍ necesitamos buscar.
        fechas_a_buscar = funcion_chequear_frescura_48h(
            url_info.id_plataforma_url, 
            fecha_inicio, 
            fecha_fin
        )

        # 5. OBTENER EL ROBOT ESPECÍFICO (FACTORY PATTERN)
        # Usa el RobotFactory para instanciar dinámicamente el robot correcto
        # basado en la columna 'plataforma' de la BBDD.
        TRY:
            robot_especifico = RobotFactory.crear_robot(url_info.plataforma)
        CATCH (Error_Plataforma_No_Soportada):
            MOSTRAR_ERROR_STREAMLIT(f"Plataforma '{url_info.plataforma}' no soportada.")
            CONTINUAR_BUCLE # Salta a la siguiente URL

        # 6. BUCLE POR CADA FECHA (Trabajo real)
        PARA CADA fecha EN fechas_a_buscar:
            
            # (Esta es la parte que se actualiza "en vivo" en la tabla temporal de Streamlit)
            MOSTRAR_EN_STREAMLIT(f"Buscando {url_info.plataforma} para {fecha}...")

            # 7. EJECUTAR EL ROBOT ESPECÍFICO (CON RETRY LOGIC)
            # Todos los robots tienen la misma función ".buscar()"
            # Se implementa retry con exponential backoff
            intentos = 0
            max_intentos = 3
            resultado = NULO
            
            MIENTRAS intentos < max_intentos:
                TRY:
                    resultado = robot_especifico.buscar(
                        navegador, 
                        url_info.url, 
                        fecha
                    )
                    BREAK # Éxito, salir del bucle
                CATCH (Error_Bloqueo O Error_CAPTCHA):
                    intentos += 1
                    SI intentos < max_intentos:
                        tiempo_espera = 2 ** intentos # Exponential backoff: 2s, 4s, 8s
                        ESPERAR(tiempo_espera)
                    SINO:
                        resultado = {
                            "error": "BLOQUEO/CAPTCHA Detectado (máx intentos)", 
                            "precio": 0, 
                            "noches": 0,
                            "detalles": NULO
                        }
            
            # 8. GUARDAR EN BASE DE DATOS (Q12)
            # Esta función usa el UPSERT definido en Fase 1.
            funcion_guardar_resultado_en_db(
                url_info.id_plataforma_url, 
                fecha, 
                resultado
            )

            # 9. PRUDENCIA (Q6)
            # Pausa aleatoria entre 3 y 8 segundos para no saturar.
            ESPERAR(tiempo_aleatorio(3, 8)) 

    # 10. CERRAR NAVEGADOR
    CERRAR_NAVEGADOR(navegador)
    MOSTRAR_EN_STREAMLIT("¡Proceso completado!")
```

-----

#### 2\. El Factory (Factory Pattern)

Antes de definir los robots, necesitamos un "Factory" que los instancie dinámicamente:

```python
# --- Factory para crear robots (Ej: scrapers/robot_factory.py) ---

CLASE RobotFactory:
    
    @staticmethod
    FUNCION crear_robot(nombre_plataforma):
        """
        Retorna una instancia del robot correcto según el nombre de la plataforma.
        Lanza Error_Plataforma_No_Soportada si no existe.
        """
        robots_disponibles = {
            "Booking": BookingRobot,
            "Airbnb": AirbnbRobot,
            "Vrbo": VrboRobot  # Futuro
        }
        
        SI nombre_plataforma EN robots_disponibles:
            RETORNAR robots_disponibles[nombre_plataforma]()
        SINO:
            LANZAR Error_Plataforma_No_Soportada(
                f"No existe robot para '{nombre_plataforma}'. "
                f"Plataformas soportadas: {lista(robots_disponibles.keys())}"
            )
```

-----

#### 3\. Los Robots (Strategy Pattern)

Definimos una "plantilla" (una Clase Abstracta o Interfaz) que *todos* los robots deben seguir. Esto asegura que el Orquestador pueda usarlos de forma intercambiable.

```python
# --- Plantilla que todos los robots DEBEN implementar (Ej: interfaces/robot_interface.py) ---

CLASE InterfazRobot:
    FUNCION buscar(navegador, url_base, fecha_checkin):
        """
        Intenta encontrar un precio usando la lógica 3->2->1 noches.
        Debe retornar un diccionario con la siguiente estructura:
        { 
            "precio": (float), 
            "noches": (int 1, 2, o 3), 
            "detalles": { "limpieza": str, "impuestos": str, "desayuno": str },
            "error": (str o NULO)
        }
        """
        PASAR # Esto será implementado por cada robot específico
```

A continuación, se definen los módulos de robot específicos.

```python
# --- Robot Específico 1 (Ej: scrapers/robots/booking_robot.py) ---

CLASE BookingRobot IMPLEMENTA InterfazRobot:
    
    FUNCION __init__(self):
        # Carga selectores desde config/selectors.json
        self.selectores = cargar_selectores("Booking")
    
    FUNCION buscar(navegador, url_base, fecha_checkin):
        
        intentos_noches = [3, 2, 1] # (Q2) Lógica de búsqueda
        
        PARA CADA noches EN intentos_noches:
            # 1. Construir URL de Booking
            url_busqueda = self.construir_url_booking(url_base, fecha_checkin, noches)
            
            pagina = navegador.NUEVA_PAGINA()
            pagina.IR_A(url_busqueda)
            
            # 2. Detectar estado (LÓGICA SOLO DE BOOKING)
            SI (pagina.CONTIENE_TEXTO("Verifica que eres humano")):
                pagina.CERRAR()
                LANZAR Error_Bloqueo("Booking detectó un CAPTCHA")
                
            SI (pagina.CONTIENE_SELECTOR("[data-testid='calendar-unavailable']")):
                pagina.CERRAR()
                CONTINUAR_BUCLE # Intenta con (noches - 1)

            # 3. Éxito! Extraer precio (USA SELECTORES EXTERNALIZADOS)
            TRY:
                # Intenta 3 selectores alternativos (redundancia)
                precio_str = NULO
                PARA CADA selector EN self.selectores["precio"]:
                    TRY:
                        precio_str = pagina.OBTENER_TEXTO(selector)
                        BREAK
                    CATCH:
                        CONTINUAR
                
                SI precio_str ES NULO:
                    LANZAR Error("No se encontró precio con ningún selector")
                
                precio_total = convertir_a_numero(precio_str)
            CATCH:
                pagina.CERRAR()
                CONTINUAR_BUCLE # No se encontró el precio, intentar con menos noches
            
            # 4. Extraer detalles (LÓGICA SOLO DE BOOKING)
            detalles = {
                "limpieza": "No Informa", # Booking rara vez lo separa
                "impuestos": "Sí" SI pagina.CONTIENE_TEXTO("incluye impuestos") SINO "No Informa",
                "desayuno": "Sí" SI pagina.CONTIENE_TEXTO("Desayuno incluido") SINO "No Informa"
            }
            
            pagina.CERRAR()
            RETORNAR { 
                "precio": precio_total / noches, 
                "noches": noches, 
                "detalles": detalles,
                "error": NULO
            }
            
        # 6. FRACASO TOTAL (Q19)
        RETORNAR { 
            "precio": 0, 
            "noches": 0, 
            "detalles": NULO,
            "error": "No disponible (3, 2 y 1 noche fallaron)"
        }

    FUNCION construir_url_booking(url, fecha, noches):
        # Lógica para añadir &checkin=... &checkout=... a la URL de Booking
        PASAR
```

```python
# --- Robot Específico 2 (Ej: scrapers/robots/airbnb_robot.py) ---

CLASE AirbnbRobot IMPLEMENTA InterfazRobot:

    FUNCION __init__(self):
        # Carga selectores desde config/selectors.json
        self.selectores = cargar_selectores("Airbnb")

    FUNCION buscar(navegador, url_base, fecha_checkin):
        
        intentos_noches = [3, 2, 1]
        
        PARA CADA noches EN intentos_noches:
            # 1. Construir URL de Airbnb
            url_busqueda = self.construir_url_airbnb(url_base, fecha_checkin, noches)
            
            pagina = navegador.NUEVA_PAGINA()
            pagina.IR_A(url_busqueda)
            ESPERAR(tiempo_aleatorio(2, 4)) # Airbnb necesita más JS
            
            # 2. Detectar estado (LÓGICA SOLO DE AIRBNN)
            SI (pagina.CONTIENE_TEXTO("Confirma que no eres un robot")):
                pagina.CERRAR()
                LANZAR Error_Bloqueo("Airbnb detectó un CAPTCHA")
            
            SI (pagina.CONTIENE_TEXTO("no está disponible para estas fechas")):
                pagina.CERRAR()
                CONTINUAR_BUCLE

            # 3. Éxito! Extraer precio (LÓGICA SOLO DE AIRBNB)
            TRY:
                # El selector de Airbnb es ofuscado, ej: '_a1g1g1'
                precio_str = pagina.OBTENER_TEXTO("._a1g1g1 > span") 
                precio_total = convertir_a_numero(precio_str)
            CATCH:
                pagina.CERRAR()
                CONTINUAR_BUCLE
            
            # 4. Extraer detalles (LÓGICA SOLO DE AIRBNB)
            detalles = {
                "limpieza": "Sí" SI pagina.CONTIENE_TEXTO("Tarifa de limpieza") SINO "No Informa",
                "impuestos": "Sí" SI pagina.CONTIENE_TEXTO("Tarifa de servicio") SINO "No Informa",
                "desayuno": "No Informa" # Airbnb no lo detalla así
            }
            
            pagina.CERRAR()
            RETORNAR { 
                "precio": precio_total / noches, 
                "noches": noches, 
                "detalles": detalles,
                "error": NULO
            }

        # 6. FRACASO TOTAL (Q19)
        RETORNAR { 
            "precio": 0, 
            "noches": 0, 
            "detalles": NULO,
            "error": "No disponible (3, 2 y 1 noche fallaron)"
        }

    FUNCION construir_url_airbnb(url, fecha, noches):
        # Lógica para añadir ?checkin=... &checkout=... a la URL de Airbnb
        PASAR
```

-----

#### 4\. Configuración de Selectores (Externalizado)

Para facilitar el mantenimiento, todos los selectores CSS/XPath se almacenan en un archivo JSON:

```json
// --- scrapers/config/selectors.json ---
{
  "Booking": {
    "precio": [
      "[data-testid='price-label']",
      ".priceDisplay",
      "span.price-value"
    ],
    "no_disponible": [
      "[data-testid='calendar-unavailable']",
      ".not-available-message"
    ],
    "captcha": [
      ".captcha-container",
      "#challenge-running"
    ]
  },
  "Airbnb": {
    "precio": [
      "._1jo4hgw",
      "span._tyxjp1",
      "._14y1gc"
    ],
    "no_disponible": [
      "._1r4u6z8",
      ".unavailable-message"
    ],
    "captcha": [
      "#recaptcha",
      ".challenge-form"
    ]
  }
}
```

**Ventajas:**
1. **Mantenimiento sin código**: Actualizar selectores sin tocar Python.
2. **Redundancia**: Múltiples selectores alternativos por elemento.
3. **Versionado**: Historial de cambios en Git.

-----

#### 5\. Utilidades Anti-Detección

```python
# --- scrapers/utils/stealth.py ---

FUNCION configurar_navegador_stealth(playwright):
    """
    Configura el navegador para parecer humano y evadir detección básica.
    """
    navegador = playwright.chromium.launch(
        headless=TRUE,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox'
        ]
    )
    
    contexto = navegador.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        locale='es-ES',
        timezone_id='Europe/Madrid'
    )
    
    # Inyecta scripts anti-detección
    contexto.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
    """)
    
    RETORNAR navegador, contexto
```

-----

#### 6\. Funciones Auxiliares (Base de Datos)

Estas funciones manejan la lógica de lectura y escritura. Son las mismas que en el borrador anterior, ya que la lógica de la BBDD no cambia.

```python
# --- PSEUDOCÓDIGO DE FUNCIONES DE BBDD ---

FUNCION funcion_chequear_frescura_48h(id_url, inicio, fin):
    
    fechas_rango_total = generar_lista_de_fechas(inicio, fin)
    
    # Busca datos existentes
    datos_db = CONSULTAR_SQL(
        "SELECT fecha_noche, fecha_scrape 
         FROM Precios 
         WHERE id_plataforma_url = ? AND fecha_noche BETWEEN ? AND ?",
        (id_url, inicio, fin)
    )
    
    fechas_frescas_a_omitir = []
    PARA CADA fila EN datos_db:
        # (Q12) Si el dato tiene MENOS de 48h, lo omitimos.
        SI ( (AHORA - fila.fecha_scrape) < 48 HORAS ):
            fechas_frescas_a_omitir.AGREGAR(fila.fecha_noche)
            
    # Restamos las fechas frescas de las fechas totales
    lista_de_tareas = fechas_rango_total MENOS fechas_frescas_a_omitir
    RETORNAR lista_de_tareas

# ---

FUNCION funcion_guardar_resultado_en_db(id_url, fecha, resultado):
    
    # (Q19) Lógica de Ocupación
    precio_final = resultado["precio"]
    esta_ocupado = (precio_final == 0)

    # Prepara los datos para el UPSERT
    # (Manejo de NULO si "detalles" no vino por un error)
    detalles = resultado["detalles"] SI resultado["detalles"] SINO {}
    
    datos = {
        "id_url": id_url,
        "fecha": fecha,
        "precio": precio_final,
        "ocupado": esta_ocupado,
        "limpieza": detalles.OBTENER("limpieza", "No Informa"),
        "impuestos": detalles.OBTENER("impuestos", "No Informa"),
        "desayuno": detalles.OBTENER("desayuno", "No Informa"),
        "fecha_scrape": AHORA,
        "noches_encontradas": resultado["noches"],
        "error": resultado["error"]
    }

    # EJECUTAR EL COMANDO UPSERT (Definido en Fase 1)
    EJECUTAR_SQL(
        "INSERT INTO Precios (...) VALUES (...) 
         ON CONFLICT(id_plataforma_url, fecha_noche) 
         DO UPDATE SET ...",
        datos
    )
```