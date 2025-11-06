"""
Orquestador Principal de Scraping
Gestiona la cola de trabajos, lógica de 48h, delegación a robots y rate limiting
"""
import logging
from datetime import datetime
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass

from scrapers.robot_factory import RobotFactory, PlatformNotSupportedError
from scrapers.utils.stealth import configurar_navegador_stealth
from scrapers.utils.retry import esperar_aleatorio, retry_con_backoff
from database.db_manager import get_db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ResultadoScraping:
    """Estructura para almacenar resultados de scraping"""
    id_plataforma_url: int
    plataforma: str
    fecha_noche: datetime
    precio: float
    noches: int
    detalles: Optional[Dict]
    error: Optional[str]
    timestamp: datetime


class ScrapingOrchestrator:
    """
    Orquestador central que gestiona todo el proceso de scraping.
    Implementa lógica de negocio: 48h, rate limiting, retry logic.
    """
    
    def __init__(self, callback_progreso: Optional[Callable] = None):
        """
        Args:
            callback_progreso: Función opcional para reportar progreso en tiempo real
                              Firma: callback(mensaje: str, progreso: float, resultado: ResultadoScraping)
        """
        self.db = get_db()
        self.callback_progreso = callback_progreso
        self.resultados: List[ResultadoScraping] = []
    
    def ejecutar(
        self,
        id_establecimiento: int,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[ResultadoScraping]:
        """
        Ejecuta el proceso completo de scraping para un establecimiento.
        
        Args:
            id_establecimiento: ID del establecimiento a scrapear
            fecha_inicio: Fecha de inicio del rango
            fecha_fin: Fecha de fin del rango
            
        Returns:
            Lista de resultados del scraping
        """
        logger.info(f"=== INICIANDO SCRAPING ===")
        logger.info(f"Establecimiento ID: {id_establecimiento}")
        logger.info(f"Rango: {fecha_inicio.date()} a {fecha_fin.date()}")
        
        self.resultados = []
        
        # 1. OBTENER TAREAS (URLs activas)
        urls_activas = self.db.get_urls_activas_by_establecimiento(id_establecimiento)
        
        if not urls_activas:
            logger.warning("No hay URLs activas para scrapear")
            self._reportar_progreso("No hay URLs activas", 1.0, None)
            return []
        
        logger.info(f"URLs activas encontradas: {len(urls_activas)}")
        
        # 2. INICIAR NAVEGADOR (UNA SOLA VEZ - EFICIENCIA)
        logger.info("Iniciando navegador con modo stealth...")
        browser, context = configurar_navegador_stealth()
        
        try:
            # 3. BUCLE POR CADA URL
            total_urls = len(urls_activas)
            
            for idx, url_info in enumerate(urls_activas, 1):
                logger.info(f"\n--- URL {idx}/{total_urls}: {url_info['plataforma']} ---")
                self._reportar_progreso(
                    f"Procesando {url_info['plataforma']} ({idx}/{total_urls})",
                    (idx - 1) / total_urls,
                    None
                )
                
                # 4. APLICAR LÓGICA DE 48 HORAS
                fechas_a_buscar = self.db.get_fechas_a_scrapear(
                    url_info['id_plataforma_url'],
                    fecha_inicio,
                    fecha_fin
                )
                
                logger.info(f"Fechas a scrapear: {len(fechas_a_buscar)} (después de filtro 48h)")
                
                if not fechas_a_buscar:
                    logger.info("Todos los datos están frescos (< 48h). Saltando...")
                    continue
                
                # 5. OBTENER EL ROBOT ESPECÍFICO (FACTORY PATTERN)
                try:
                    robot = RobotFactory.crear_robot(url_info['plataforma'])
                except PlatformNotSupportedError as e:
                    logger.error(f"Plataforma no soportada: {e}")
                    self._reportar_progreso(
                        f"❌ {url_info['plataforma']}: Plataforma no soportada",
                        idx / total_urls,
                        None
                    )
                    continue
                
                # 6. BUCLE POR CADA FECHA
                total_fechas = len(fechas_a_buscar)
                for fecha_idx, fecha in enumerate(fechas_a_buscar, 1):
                    mensaje = f"[{url_info['plataforma']}] {fecha.date()} ({fecha_idx}/{total_fechas})"
                    self._reportar_progreso(
                        mensaje,
                        (idx - 1 + fecha_idx / total_fechas) / total_urls,
                        None
                    )
                    
                    # 7. EJECUTAR EL ROBOT CON RETRY LOGIC
                    resultado_scrape = self._ejecutar_con_retry(
                        robot,
                        browser,
                        url_info['url'],
                        fecha
                    )
                    
                    # 8. GUARDAR EN BASE DE DATOS
                    self._guardar_resultado(
                        url_info['id_plataforma_url'],
                        url_info['plataforma'],
                        fecha,
                        resultado_scrape
                    )
                    
                    # 9. RATE LIMITING (PRUDENCIA)
                    if fecha_idx < total_fechas:  # No esperar después de la última fecha
                        esperar_aleatorio()
        
        finally:
            # 10. CERRAR NAVEGADOR
            logger.info("\nCerrando navegador...")
            context.close()
            browser.close()
        
        logger.info(f"\n=== SCRAPING COMPLETADO ===")
        logger.info(f"Resultados totales: {len(self.resultados)}")
        self._reportar_progreso("✅ Proceso completado", 1.0, None)
        
        return self.resultados
    
    def _ejecutar_con_retry(
        self,
        robot,
        browser,
        url: str,
        fecha: datetime,
        max_intentos: int = 3
    ) -> Dict:
        """
        Ejecuta el robot con lógica de retry y exponential backoff.
        
        Returns:
            Diccionario con el resultado del scraping
        """
        import time
        
        for intento in range(1, max_intentos + 1):
            try:
                resultado = robot.buscar(browser, url, fecha)
                return resultado
                
            except Exception as e:
                logger.error(f"Error en intento {intento}/{max_intentos}: {e}")
                
                if intento == max_intentos:
                    # Último intento fallido
                    return {
                        "precio": 0,
                        "noches": 0,
                        "detalles": None,
                        "error": f"Error después de {max_intentos} intentos: {str(e)}"
                    }
                
                # Exponential backoff
                tiempo_espera = 2 ** intento  # 2s, 4s, 8s
                logger.info(f"Reintentando en {tiempo_espera}s...")
                time.sleep(tiempo_espera)
        
        # No debería llegar aquí, pero por seguridad
        return {
            "precio": 0,
            "noches": 0,
            "detalles": None,
            "error": "Error desconocido"
        }
    
    def _guardar_resultado(
        self,
        id_plataforma_url: int,
        plataforma: str,
        fecha: datetime,
        resultado_scrape: Dict
    ):
        """
        Guarda el resultado en la base de datos y en la lista de resultados.
        """
        # Extraer datos del resultado
        precio = resultado_scrape.get('precio', 0)
        noches = resultado_scrape.get('noches', 0)
        detalles = resultado_scrape.get('detalles', {})
        error = resultado_scrape.get('error')
        
        # Guardar en BD usando UPSERT
        try:
            self.db.upsert_precio(
                id_plataforma_url=id_plataforma_url,
                fecha_noche=fecha,
                precio_base=precio,
                noches_encontradas=noches,
                incluye_limpieza=detalles.get('limpieza', 'No Informa') if detalles else 'No Informa',
                incluye_impuestos=detalles.get('impuestos', 'No Informa') if detalles else 'No Informa',
                ofrece_desayuno=detalles.get('desayuno', 'No Informa') if detalles else 'No Informa',
                error_log=error
            )
            logger.info(f"✓ Guardado: {fecha.date()} - Precio: ${precio:.2f} (Noches: {noches})")
            
        except Exception as e:
            logger.error(f"Error guardando en BD: {e}")
        
        # Crear resultado estructurado
        resultado = ResultadoScraping(
            id_plataforma_url=id_plataforma_url,
            plataforma=plataforma,
            fecha_noche=fecha,
            precio=precio,
            noches=noches,
            detalles=detalles,
            error=error,
            timestamp=datetime.now()
        )
        
        self.resultados.append(resultado)
        
        # Reportar progreso con el resultado
        self._reportar_progreso(None, None, resultado)
    
    def _reportar_progreso(
        self,
        mensaje: Optional[str],
        progreso: Optional[float],
        resultado: Optional[ResultadoScraping]
    ):
        """Llama al callback de progreso si está definido"""
        if self.callback_progreso:
            try:
                self.callback_progreso(mensaje, progreso, resultado)
            except Exception as e:
                logger.warning(f"Error en callback de progreso: {e}")


# Función helper para uso directo
def ejecutar_scraping(
    id_establecimiento: int,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    callback_progreso: Optional[Callable] = None
) -> List[ResultadoScraping]:
    """
    Función helper para ejecutar scraping directamente.
    
    Args:
        id_establecimiento: ID del establecimiento
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin
        callback_progreso: Callback opcional para reportar progreso
        
    Returns:
        Lista de resultados
    """
    orchestrator = ScrapingOrchestrator(callback_progreso)
    return orchestrator.ejecutar(id_establecimiento, fecha_inicio, fecha_fin)
