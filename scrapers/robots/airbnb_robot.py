"""
Robot específico para scrapear Airbnb
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import random

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeout

from scrapers.base_robot import BaseRobot
from scrapers.utils.url_builder import URLBuilder
from scrapers.utils.retry import esperar_aleatorio

logger = logging.getLogger(__name__)


class AirbnbRobot(BaseRobot):
    """
    Robot para scrapear precios de Airbnb.
    Implementa la lógica 3->2->1 noches y manejo de errores.
    """
    
    def __init__(self):
        super().__init__('Airbnb')
        self._cargar_selectores()
    
    def _cargar_selectores(self):
        """Carga selectores desde el archivo JSON"""
        config_path = Path(__file__).parent.parent / 'config' / 'selectors.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.selectores = config.get('Airbnb', {})
    
    def construir_url(self, url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """Construye URL de Airbnb con parámetros de búsqueda"""
        return URLBuilder.airbnb_url(url_base, fecha_checkin, noches)
    
    def buscar(self, browser: Browser, url_base: str, fecha_checkin: datetime) -> Dict:
        """
        Busca precio en Airbnb usando lógica 3->2->1 noches.
        
        Returns:
            Diccionario con precio, noches, detalles y error (si aplica)
        """
        intentos_noches = [3, 2, 1]
        
        for noches in intentos_noches:
            logger.info(f"[Airbnb] Buscando {noches} noche(s) para {fecha_checkin.date()}")
            
            # Construir URL
            url_busqueda = self.construir_url(url_base, fecha_checkin, noches)
            
            # Crear nueva página
            context = browser.contexts[0]
            page = context.new_page()
            
            try:
                # Navegar a la URL
                page.goto(url_busqueda, wait_until='domcontentloaded', timeout=30000)
                
                # Airbnb necesita más tiempo para cargar JavaScript
                page.wait_for_timeout(random.randint(3000, 5000))
                
                # Detectar bloqueo/CAPTCHA
                if self.detectar_bloqueo(page):
                    logger.warning("[Airbnb] CAPTCHA o bloqueo detectado")
                    page.close()
                    return {
                        "precio": 0,
                        "noches": 0,
                        "detalles": None,
                        "error": "CAPTCHA/Bloqueo detectado en Airbnb"
                    }
                
                # Detectar si no está disponible
                if self._detectar_no_disponible(page):
                    logger.debug(f"[Airbnb] No disponible para {noches} noche(s)")
                    page.close()
                    continue
                
                # Extraer precio
                precio_str = self.extraer_precio_con_selectores_alternativos(
                    page, 
                    self.selectores.get('precio', [])
                )
                
                if not precio_str:
                    logger.debug(f"[Airbnb] No se encontró precio para {noches} noche(s)")
                    page.close()
                    continue
                
                # Convertir precio
                precio_total = self.limpiar_precio(precio_str)
                if precio_total == 0:
                    page.close()
                    continue
                
                # Extraer detalles
                detalles = self._extraer_detalles(page)
                
                page.close()
                
                # ¡Éxito!
                precio_por_noche = precio_total / noches
                logger.info(f"[Airbnb] Precio encontrado: {precio_por_noche:.2f} ({noches} noche(s))")
                
                return {
                    "precio": round(precio_por_noche, 2),
                    "noches": noches,
                    "detalles": detalles,
                    "error": None
                }
                
            except PlaywrightTimeout:
                logger.error(f"[Airbnb] Timeout navegando a {url_busqueda}")
                page.close()
                continue
                
            except Exception as e:
                logger.error(f"[Airbnb] Error inesperado: {e}")
                page.close()
                continue
        
        # FRACASO TOTAL
        logger.warning("[Airbnb] No disponible para ninguna duración (3, 2, 1 noches)")
        return {
            "precio": 0,
            "noches": 0,
            "detalles": None,
            "error": "No disponible (todas las búsquedas fallaron)"
        }
    
    def _detectar_no_disponible(self, page: Page) -> bool:
        """Detecta si el alojamiento no está disponible"""
        for selector in self.selectores.get('no_disponible', []):
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        return False
    
    def _extraer_detalles(self, page: Page) -> Dict[str, str]:
        """
        Extrae detalles adicionales (limpieza, impuestos, desayuno).
        
        Returns:
            Diccionario con los detalles encontrados
        """
        detalles = {
            "limpieza": "No Informa",
            "impuestos": "No Informa",
            "desayuno": "No Informa"
        }
        
        # En Airbnb, la tarifa de limpieza está separada
        for selector in self.selectores.get('limpieza_incluida', []):
            try:
                if page.locator(selector).count() > 0:
                    detalles["limpieza"] = "Separada"  # Airbnb la cobra aparte
                    break
            except:
                continue
        
        # Verificar tarifa de servicio (impuestos)
        for selector in self.selectores.get('impuestos_incluidos', []):
            try:
                if page.locator(selector).count() > 0:
                    detalles["impuestos"] = "Separados"
                    break
            except:
                continue
        
        # Airbnb rara vez especifica desayuno en el precio
        # Lo dejamos como "No Informa"
        
        return detalles
