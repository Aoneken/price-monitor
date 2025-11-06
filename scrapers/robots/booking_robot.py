"""
Robot específico para scrapear Booking.com
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeout

from scrapers.base_robot import BaseRobot
from scrapers.utils.url_builder import URLBuilder
from scrapers.utils.retry import esperar_aleatorio

logger = logging.getLogger(__name__)


class BookingRobot(BaseRobot):
    """
    Robot para scrapear precios de Booking.com.
    Implementa la lógica 3->2->1 noches y manejo de errores.
    """
    
    def __init__(self):
        super().__init__('Booking')
        self._cargar_selectores()
    
    def _cargar_selectores(self):
        """Carga selectores desde el archivo JSON"""
        config_path = Path(__file__).parent.parent / 'config' / 'selectors.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.selectores = config.get('Booking', {})
    
    def construir_url(self, url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """Construye URL de Booking con parámetros de búsqueda"""
        return URLBuilder.booking_url(url_base, fecha_checkin, noches)
    
    def buscar(self, browser: Browser, url_base: str, fecha_checkin: datetime) -> Dict:
        """
        Busca precio en Booking.com usando lógica 3->2->1 noches.
        
        Returns:
            Diccionario con precio, noches, detalles y error (si aplica)
        """
        intentos_noches = [3, 2, 1]  # Lógica de búsqueda
        
        for noches in intentos_noches:
            logger.info(f"[Booking] Buscando {noches} noche(s) para {fecha_checkin.date()}")
            
            # Construir URL
            url_busqueda = self.construir_url(url_base, fecha_checkin, noches)
            
            # Crear nueva página
            context = browser.contexts[0]
            page = context.new_page()
            
            try:
                # Navegar a la URL
                page.goto(url_busqueda, wait_until='domcontentloaded', timeout=30000)
                
                # Esperar un poco para que cargue JavaScript
                page.wait_for_timeout(random.randint(2000, 4000))
                
                # Detectar bloqueo/CAPTCHA
                if self.detectar_bloqueo(page):
                    logger.warning("[Booking] CAPTCHA o bloqueo detectado")
                    page.close()
                    return {
                        "precio": 0,
                        "noches": 0,
                        "detalles": None,
                        "error": "CAPTCHA/Bloqueo detectado en Booking"
                    }
                
                # Detectar si no está disponible
                if self._detectar_no_disponible(page):
                    logger.debug(f"[Booking] No disponible para {noches} noche(s)")
                    page.close()
                    continue  # Intentar con menos noches
                
                # Extraer precio
                precio_str = self.extraer_precio_con_selectores_alternativos(
                    page, 
                    self.selectores.get('precio', [])
                )
                
                if not precio_str:
                    logger.debug(f"[Booking] No se encontró precio para {noches} noche(s)")
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
                logger.info(f"[Booking] Precio encontrado: {precio_por_noche:.2f} ({noches} noche(s))")
                
                return {
                    "precio": round(precio_por_noche, 2),
                    "noches": noches,
                    "detalles": detalles,
                    "error": None
                }
                
            except PlaywrightTimeout:
                logger.error(f"[Booking] Timeout navegando a {url_busqueda}")
                page.close()
                continue
                
            except Exception as e:
                logger.error(f"[Booking] Error inesperado: {e}")
                page.close()
                continue
        
        # FRACASO TOTAL: No se encontró precio en ninguna búsqueda (3, 2, 1 noches)
        logger.warning("[Booking] No disponible para ninguna duración (3, 2, 1 noches)")
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
        
        # Verificar limpieza
        for selector in self.selectores.get('limpieza_incluida', []):
            try:
                if page.locator(selector).count() > 0:
                    detalles["limpieza"] = "Sí"
                    break
            except:
                continue
        
        # Verificar impuestos
        for selector in self.selectores.get('impuestos_incluidos', []):
            try:
                if page.locator(selector).count() > 0:
                    detalles["impuestos"] = "Sí"
                    break
            except:
                continue
        
        # Verificar desayuno
        for selector in self.selectores.get('desayuno_incluido', []):
            try:
                if page.locator(selector).count() > 0:
                    detalles["desayuno"] = "Sí"
                    break
            except:
                continue
        
        return detalles


# Importar random para jitter
import random
