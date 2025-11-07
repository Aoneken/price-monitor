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
                logger.info(f"[Airbnb] Navegando a URL...")
                page.goto(url_busqueda, wait_until='domcontentloaded', timeout=90000)
                
                # Airbnb necesita MÁS tiempo para cargar JavaScript (mejorado desde main)
                logger.info(f"[Airbnb] Esperando carga de contenido...")
                page.wait_for_timeout(8000)
                
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
                
                # Detectar si no está disponible ANTES de buscar precio
                if self._detectar_no_disponible(page):
                    logger.debug(f"[Airbnb] No disponible para {noches} noche(s)")
                    page.close()
                    continue
                
                # Extraer precio con método mejorado
                logger.info(f"[Airbnb] Buscando precio...")
                precio_str = self._extraer_precio_mejorado(page)
                
                if not precio_str:
                    logger.debug(f"[Airbnb] No se encontró precio para {noches} noche(s)")
                    # Guardar screenshot para debug
                    self._guardar_debug(page, fecha_checkin, noches)
                    page.close()
                    continue
                
                # Convertir precio
                precio_total = self.limpiar_precio(precio_str)
                if precio_total == 0:
                    logger.debug(f"[Airbnb] Precio extraído es 0 para {noches} noche(s)")
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
        # Primero intentar con selectores
        for selector in self.selectores.get('no_disponible', []):
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        # También buscar en el texto de la página
        try:
            page_text = page.inner_text('body')
            unavailable_indicators = [
                'No disponible',
                'no está disponible',
                'not available',
                'sold out',
                'completamente reservado',
                'already booked',
                'Este alojamiento no está disponible',
                'These dates are unavailable'
            ]
            
            return any(indicator in page_text for indicator in unavailable_indicators)
        except:
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
    
    def _extraer_precio_mejorado(self, page: Page) -> str:
        """
        Extrae precio usando selectores mejorados de la rama main
        """
        # Selectores actualizados para Airbnb (2025)
        selectores_mejorados = [
            'div[data-section-id="BOOK_IT_SIDEBAR"] span[class*="_14y1gc"]',
            'span._tyxjp1',
            'span._1k4xcdh',
            'div._1jo4hgw',
            'span[class*="price"]',
            'div[class*="PriceLockup"]',
            'span[class*="_tyxjp1"]',
            'div[class*="_1y74zjx"]',
            'span[aria-hidden="true"]',
        ]
        
        # Intentar con selectores mejorados primero
        for selector in selectores_mejorados:
            try:
                elementos = page.query_selector_all(selector)
                for elemento in elementos:
                    texto = elemento.inner_text()
                    if texto and ('$' in texto or 'USD' in texto) and any(char.isdigit() for char in texto):
                        logger.debug(f"[Airbnb] Precio encontrado con selector: {selector}")
                        return texto
            except:
                continue
        
        # Luego intentar con los selectores originales del JSON
        precio = self.extraer_precio_con_selectores_alternativos(
            page, 
            self.selectores.get('precio', [])
        )
        if precio:
            return precio
        
        # Finalmente, buscar en el texto de toda la página
        try:
            page_text = page.inner_text('body')
            
            # Buscar patrones de precio en el texto
            import re
            price_patterns = [
                r'\$\s*([0-9,]+)\s*USD',
                r'USD\s*\$?\s*([0-9,]+)',
                r'\$([0-9,]+)\s*total',
                r'Total\s*\$([0-9,]+)',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    logger.debug(f"[Airbnb] Precio encontrado con regex: {pattern}")
                    return match.group(0)
        except:
            pass
        
        return None
    
    def _guardar_debug(self, page: Page, fecha: datetime, noches: int):
        """Guarda screenshot y HTML para debugging"""
        try:
            import os
            from pathlib import Path
            
            debug_dir = Path(__file__).parent.parent.parent / 'debug'
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%H%M%S")
            fecha_str = fecha.strftime("%Y%m%d")
            
            screenshot_path = debug_dir / f'airbnb_{fecha_str}_{noches}n_{timestamp}.png'
            html_path = debug_dir / f'airbnb_{fecha_str}_{noches}n_{timestamp}.html'
            
            page.screenshot(path=str(screenshot_path))
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
            logger.info(f"[Airbnb] Debug guardado en {screenshot_path}")
        except Exception as e:
            logger.warning(f"[Airbnb] No se pudo guardar debug: {e}")
