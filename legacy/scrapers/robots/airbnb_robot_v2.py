"""
Robot Airbnb V2 - SOLUCIÓN ROBUSTA Y RÁPIDA
Basado en extractor robusto compartido
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeout

from scrapers.base_robot import BaseRobot
from scrapers.utils.url_builder import URLBuilder
from scrapers.extraction_engine import crear_extractor_airbnb, NetworkAPIStrategy

logger = logging.getLogger(__name__)


class AirbnbRobotV2(BaseRobot):
    """
    Robot V2 para Airbnb con extracción super robusta.
    
    ESTRATEGIA NUEVA:
    1. Espera mínima (solo 2s) para carga básica
    2. Extracción desde JSON embebido en la página (más confiable)
    3. Fallback a múltiples estrategias DOM
    4. Validación estricta de precios
    """
    
    def __init__(self):
        super().__init__('Airbnb')
        self.debug_enabled = True
    
    def construir_url(self, url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """Compatibilidad con BaseRobot: retorna la URL principal"""
        return URLBuilder.airbnb_url(url_base, fecha_checkin, noches)

    def construir_urls(self, url_base: str, fecha_checkin: datetime, noches: int):
        """Genera URLs de Airbnb (principal + fallback)"""
        return URLBuilder.airbnb_url_variants(url_base, fecha_checkin, noches)
    
    def buscar(self, browser: Browser, url_base: str, fecha_checkin: datetime) -> Dict:
        """
        Busca precio usando lógica 3->2->1 noches con estrategia robusta.
        """
        intentos_noches = [3, 2, 1]
        extractor = crear_extractor_airbnb()
        network_strategy = None
        for strategy in extractor.strategies:
            if isinstance(strategy, NetworkAPIStrategy):
                network_strategy = strategy
                break
        
        for noches in intentos_noches:
            logger.info(f"[Airbnb V2] Buscando {noches} noche(s) para {fecha_checkin.date()}")
            
            for url_busqueda in self.construir_urls(url_base, fecha_checkin, noches):
                context = browser.contexts[0]
                page = context.new_page()
                try:
                    if network_strategy:
                        network_strategy.captured_responses.clear()
                        network_strategy.setup_interception(page)
                    logger.info(f"[Airbnb V2] Navegando...")
                    page.goto(url_busqueda, wait_until='domcontentloaded', timeout=60000)
                    logger.info(f"[Airbnb V2] Esperando carga básica (2s)...")
                    page.wait_for_timeout(2000)
                
                    if self.detectar_bloqueo(page):
                        logger.warning("[Airbnb V2] CAPTCHA detectado")
                        page.close()
                        return {
                            "precio": 0,
                            "noches": 0,
                            "detalles": None,
                            "error": "CAPTCHA/Bloqueo detectado"
                        }
                
                    if self._detectar_no_disponible(page):
                        logger.debug(f"[Airbnb V2] No disponible para {noches} noche(s)")
                        page.close()
                        continue
                
                    price_data = extractor.extract(page, noches=noches)
                    if price_data:
                        detalles = price_data.detalles if price_data.detalles else self._extraer_detalles_basico(page)
                        page.close()
                        logger.info(f"[Airbnb V2] ✅ Precio encontrado: ${price_data.precio_por_noche:.2f}/noche ({noches}n)")
                        return {
                            "precio": round(price_data.precio_por_noche, 2),
                            "noches": noches,
                            "detalles": detalles,
                            "error": None
                        }
                    logger.debug(f"[Airbnb V2] Sin precio válido para {noches} noche(s) con URL actual")
                    if self.debug_enabled:
                        self._guardar_debug(page, fecha_checkin, noches)
                    page.close()
                    continue
                except PlaywrightTimeout as e:
                    logger.error(f"[Airbnb V2] Timeout: {e}")
                    page.close()
                    continue
                except Exception as e:
                    logger.error(f"[Airbnb V2] Error: {e}")
                    page.close()
                    continue
        
        # FRACASO TOTAL
        logger.warning("[Airbnb V2] No se encontró precio válido para ninguna duración")
        return {
            "precio": 0,
            "noches": 0,
            "detalles": None,
            "error": "No disponible (todas las búsquedas fallaron)"
        }
    
    def _detectar_no_disponible(self, page: Page) -> bool:
        """Detecta si no está disponible"""
        try:
            texto = page.inner_text('body')
            indicadores = [
                'no está disponible',
                'not available',
                'estas fechas no están disponibles',
                'these dates aren\'t available',
                'completamente reservado',
                'fully booked'
            ]
            return any(ind in texto.lower() for ind in indicadores)
        except:
            return False
    
    def _extraer_detalles_basico(self, page: Page) -> Dict[str, str]:
        """Extrae detalles básicos"""
        return {
            "limpieza": "No Informa",
            "impuestos": "No Informa",
            "desayuno": "No Informa"
        }
    
    def _guardar_debug(self, page: Page, fecha: datetime, noches: int):
        """Guarda screenshot y HTML para debugging"""
        try:
            debug_dir = Path(__file__).parent.parent.parent / 'debug'
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%H%M%S")
            fecha_str = fecha.strftime("%Y%m%d")
            
            screenshot_path = debug_dir / f'airbnb_v2_{fecha_str}_{noches}n_{timestamp}.png'
            html_path = debug_dir / f'airbnb_v2_{fecha_str}_{noches}n_{timestamp}.html'
            
            page.screenshot(path=str(screenshot_path))
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
            logger.info(f"[Airbnb V2] Debug guardado: {screenshot_path.name}")
        except Exception as e:
            logger.warning(f"[Airbnb V2] Error guardando debug: {e}")
