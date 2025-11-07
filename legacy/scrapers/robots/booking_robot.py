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
                logger.info(f"[Booking] Navegando a URL...")
                page.goto(url_busqueda, wait_until='networkidle', timeout=60000)
                
                # OPTIMIZADO: Reducido de 5s → 2s
                page.wait_for_timeout(2000)
                
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
                
                # Detectar si no está disponible ANTES de buscar precio
                if self._detectar_no_disponible(page):
                    logger.debug(f"[Booking] No disponible para {noches} noche(s)")
                    page.close()
                    continue  # Intentar con menos noches
                
                # Esperar a que aparezcan elementos de precio
                try:
                    page.wait_for_selector('[class*="price"], span[data-testid*="price"]', timeout=10000)
                except:
                    logger.debug(f"[Booking] No se detectaron elementos de precio")
                
                # Extraer precio con selectores actualizados
                precio_str = self._extraer_precio_mejorado(page)
                
                if not precio_str:
                    logger.debug(f"[Booking] No se encontró precio para {noches} noche(s)")
                    # Guardar screenshot para debug
                    self._guardar_debug(page, fecha_checkin, noches)
                    page.close()
                    continue
                
                # Convertir precio
                precio_total = self.limpiar_precio(precio_str)
                if precio_total == 0:
                    logger.debug(f"[Booking] Precio extraído es 0 para {noches} noche(s)")
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
                'Sold out',
                'Ocupado',
                'No rooms available',
                'No hay habitaciones disponibles',
                'We don\'t have availability',
                'Sin disponibilidad'
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
    
    def _extraer_precio_mejorado(self, page: Page) -> str:
        """
        Extrae precio usando selectores mejorados de la rama main
        """
        # Selectores actualizados para Booking (2025)
        selectores_mejorados = [
            '[data-testid="price-and-discounted-price"]',
            'span[data-testid="price-for-x-nights"]',
            'div[class*="prco-inline-block-maker-helper"]',
            'span.prco-valign-middle-helper',
            'span.prco-text-nowrap-helper',
            'div.bui-price-display__value',
            'span[aria-live="assertive"]',
        ]
        
        # Intentar con selectores mejorados primero
        for selector in selectores_mejorados:
            try:
                elementos = page.query_selector_all(selector)
                for elemento in elementos:
                    texto = elemento.inner_text()
                    if texto and ('$' in texto or 'USD' in texto or 'US$' in texto):
                        logger.debug(f"[Booking] Precio encontrado con selector: {selector}")
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
        
        # Finalmente, buscar por patrón de texto
        try:
            elementos = page.locator('text=/US\\$\\s*[0-9,]+/').all()
            if elementos:
                return elementos[0].inner_text()
            
            elementos = page.locator('text=/\\$\\s*[0-9,]+/').all()
            if elementos:
                return elementos[0].inner_text()
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
            
            screenshot_path = debug_dir / f'booking_{fecha_str}_{noches}n_{timestamp}.png'
            html_path = debug_dir / f'booking_{fecha_str}_{noches}n_{timestamp}.html'
            
            page.screenshot(path=str(screenshot_path), full_page=True)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            
            logger.info(f"[Booking] Debug guardado en {screenshot_path}")
        except Exception as e:
            logger.warning(f"[Booking] No se pudo guardar debug: {e}")


# Importar random para jitter
import random
