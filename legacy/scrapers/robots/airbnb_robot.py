"""
Robot específico para scrapear Airbnb
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import random

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeout

from scrapers.base_robot import BaseRobot
from scrapers.utils.url_builder import URLBuilder
from scrapers.extraction_engine import crear_extractor_airbnb, NetworkAPIStrategy
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
        """Compatibilidad: retorna la URL principal en formato comprobado"""
        return URLBuilder.airbnb_url(url_base, fecha_checkin, noches)

    def construir_urls(self, url_base: str, fecha_checkin: datetime, noches: int):
        """Genera URLs de Airbnb a probar (principal + fallback)"""
        return URLBuilder.airbnb_url_variants(url_base, fecha_checkin, noches)
    
    def buscar(self, browser: Browser, url_base: str, fecha_checkin: datetime) -> Dict:
        """
        Busca precio en Airbnb usando lógica 3->2->1 noches y prueba dos formatos de URL.
        """
        intentos_noches = [3, 2, 1]
        extractor = crear_extractor_airbnb()
        network_strategy = None
        for strategy in extractor.strategies:
            if isinstance(strategy, NetworkAPIStrategy):
                network_strategy = strategy
                break
        for noches in intentos_noches:
            logger.info(f"[Airbnb] Buscando {noches} noche(s) para {fecha_checkin.date()}")
            url_principal, url_alternativa = self.construir_urls(url_base, fecha_checkin, noches)
            for url_busqueda in [url_principal, url_alternativa]:
                context = browser.contexts[0]
                page = context.new_page()
                try:
                    if network_strategy:
                        network_strategy.captured_responses.clear()
                        network_strategy.setup_interception(page)
                    logger.info(f"[Airbnb] Navegando a URL...")
                    page.goto(url_busqueda, wait_until='domcontentloaded', timeout=90000)
                    logger.info(f"[Airbnb] Esperando carga de contenido...")
                    page.wait_for_timeout(3000)
                    logger.info(f"[Airbnb] Esperando renderizado de elementos de precio...")
                    precio_visible = self._esperar_precio_visible(page)
                    if not precio_visible:
                        logger.warning(f"[Airbnb] Timeout esperando elementos de precio")
                    if self.detectar_bloqueo(page):
                        logger.warning("[Airbnb] CAPTCHA o bloqueo detectado")
                        page.close()
                        return {
                            "precio": 0,
                            "noches": 0,
                            "detalles": None,
                            "error": "CAPTCHA/Bloqueo detectado en Airbnb"
                        }
                    if self._detectar_no_disponible(page):
                        logger.debug(f"[Airbnb] No disponible para {noches} noche(s)")
                        page.close()
                        continue
                    logger.info(f"[Airbnb] Probando extractor robusto...")
                    price_data = extractor.extract(page, noches=noches)
                    if not price_data:
                        logger.debug(f"[Airbnb] Extractor no obtuvo precio para {noches}n")
                        self._guardar_debug(page, fecha_checkin, noches)
                        page.close()
                        continue
                    precio_total = price_data.precio_total
                    detalles = price_data.detalles if price_data.detalles else self._extraer_detalles(page)
                    page.close()
                    precio_por_noche = price_data.precio_por_noche
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
    
    def _esperar_precio_visible(self, page: Page, timeout: int = 10000) -> bool:
        """
        Espera a que aparezca al menos UN selector de precio válido en la página.
        Esto asegura que React/JavaScript haya terminado de renderizar el contenido.
        
        Args:
            page: Página de Playwright
            timeout: Tiempo máximo de espera en milisegundos (default: 10s, antes 15s)
        
        Returns:
            True si se detectó algún elemento de precio, False si timeout
        """
        # Selectores que indican que el precio está cargado
        # Incluimos los selectores nuevos identificados por Exequiel
        selectores_precio = [
            'span.umuerxh',  # Nuevo 2025: precio con descuento
            'span.s13lowb4',  # Nuevo 2025: precio original tachado
            'span._tyxjp1',
            'span._1k4xcdh',
            'div._1jo4hgw',
            'span[class*="price"]',
            'div[class*="PriceLockup"]',
            'span[class*="_tyxjp1"]',
            'div[data-section-id="BOOK_IT_SIDEBAR"]',
        ]
        
        logger.debug(f"[Airbnb] Esperando a que aparezca elemento de precio (timeout: {timeout}ms)...")
        
        for selector in selectores_precio:
            try:
                page.wait_for_selector(selector, state='visible', timeout=timeout)
                logger.debug(f"[Airbnb] ✅ Precio visible con selector: {selector}")
                return True
            except PlaywrightTimeout:
                # Intentar con el siguiente selector
                continue
            except Exception as e:
                logger.debug(f"[Airbnb] Error esperando selector {selector}: {e}")
                continue
        
        logger.warning(f"[Airbnb] ❌ Ningún selector de precio se volvió visible en {timeout}ms")
        return False
    
    def _extraer_precio_mejorado(self, page: Page) -> Optional[str]:
        """
        Extrae precio usando selectores mejorados y validación de rango razonable.
        Solo acepta precios entre $10 y $10,000 por noche (USD).
        """
        import re
        
        def validar_precio(texto: str) -> bool:
            """Valida que el precio esté en un rango razonable"""
            try:
                # Extraer solo los dígitos del texto
                numeros = re.sub(r'[^\d]', '', texto)
                if not numeros:
                    return False
                precio = float(numeros)
                # Rango razonable: entre $10 y $10,000 por noche
                return 10 <= precio <= 10000
            except:
                return False
        
        # Selectores actualizados para Airbnb (2025)
        # Incluye selectores identificados por Exequiel en nov 2025
        selectores_mejorados = [
            'span.umuerxh',  # Nuevo 2025: precio con descuento ($254 USD)
            'span.s13lowb4',  # Nuevo 2025: precio original tachado ($310 USD)
            'span._tyxjp1',
            'span._1k4xcdh',
            'div[data-section-id="BOOK_IT_SIDEBAR"] span[class*="_14y1gc"]',
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
                    texto = elemento.inner_text().strip()
                    # Debe contener signo de dólar y números
                    if texto and '$' in texto and any(char.isdigit() for char in texto):
                        # Validar que esté en rango razonable
                        if validar_precio(texto):
                            logger.debug(f"[Airbnb] Precio encontrado con selector: {selector} -> {texto}")
                            return texto
            except:
                continue
        
        # Luego intentar con los selectores originales del JSON
        precio = self.extraer_precio_con_selectores_alternativos(
            page, 
            self.selectores.get('precio', [])
        )
        if precio and validar_precio(precio):
            return precio
        
        # Finalmente, buscar en el texto de toda la página
        try:
            page_text = page.inner_text('body')
            
            # Buscar patrones de precio en el texto
            price_patterns = [
                r'\$\s*([0-9,]+)\s*USD',
                r'USD\s*\$?\s*([0-9,]+)',
                r'\$\s*([0-9,]+)\s+por\s+noche',
                r'\$\s*([0-9,]+)\s*noche',
                r'\$\s*([0-9,]+)\s*total',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    precio_texto = match.group(0)
                    if validar_precio(precio_texto):
                        logger.debug(f"[Airbnb] Precio encontrado con regex: {pattern} -> {precio_texto}")
                        return precio_texto
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
