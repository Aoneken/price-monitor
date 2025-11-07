"""
Robot Airbnb V3 con Playwright.
"""
import time
from datetime import date
from playwright.sync_api import Browser
from src.robots.base_robot import BaseRobot
from src.parsers.airbnb_parser import AirbnbParser


class AirbnbRobotV3(BaseRobot):
    """
    Robot para scraping de Airbnb.
    
    Flujo:
    1. Navegar a URL con fechas
    2. Esperar carga del panel de precios
    3. Abrir breakdown de precios
    4. Extraer HTML del breakdown
    5. Parsear con AirbnbParser
    """
    
    def __init__(self, browser: Browser, headless: bool = True):
        super().__init__(browser, headless)
        self.parser = AirbnbParser()
    
    def scrape(
        self,
        url: str,
        check_in: date,
        check_out: date,
        property_id: str
    ) -> dict:
        """
        Scraping completo de Airbnb.
        
        Returns:
            AirbnbQuote dict
        """
        try:
            self.page = self._init_page()
            
            # Navegación
            self._navigate(url, check_in, check_out)
            
            # Extraer HTML
            html = self._extract_html()
            
            # Parsear
            quote = self.parser.build_quote(
                property_id=property_id,
                html=html,
                check_in=check_in,
                check_out=check_out,
                fuente='dom'
            )
            
            return quote
        
        finally:
            self._close_page()
    
    def _navigate(
        self,
        url: str,
        check_in: date,
        check_out: date
    ) -> None:
        """
        Navega a Airbnb con fechas seleccionadas.
        
        Estrategia anti-timeout:
        1. Navegar con wait_until='domcontentloaded' (más rápido que 'networkidle')
        2. Aumentar timeout a 60s (Airbnb es lento)
        3. Esperar múltiples selectores alternativos
        4. Si falla selector, continuar igual (el parser buscará en JSON)
        """
        # Construir URL con fechas
        base_url = url.split('?')[0]
        check_in_str = check_in.strftime('%Y-%m-%d')
        check_out_str = check_out.strftime('%Y-%m-%d')
        
        full_url = f"{base_url}?check_in={check_in_str}&check_out={check_out_str}&adults=1"
        
        # Navegar con timeout más largo y wait más permisivo
        try:
            self.page.goto(full_url, wait_until='domcontentloaded', timeout=60000)
        except Exception as e:
            # Si falla goto, intentar con load básico
            if 'timeout' in str(e).lower():
                self.page.goto(full_url, wait_until='load', timeout=60000)
            else:
                raise
        
        # Intentar esperar panel de precios con múltiples selectores
        # Si ninguno funciona, continuar igual (parser buscará en JSON)
        selectors = [
            '[data-testid*="price-item"]',
            '[data-testid="book-it-default"]',
            '[data-section-id="BOOK_IT_SIDEBAR"]',
            '.priceBreakdownModal',
            '._1lds9wb'  # Selector de reserva
        ]
        
        waited = False
        for selector in selectors:
            try:
                self.page.wait_for_selector(selector, timeout=5000)
                waited = True
                break
            except:
                continue
        
        # Dar tiempo adicional si no encontró nada
        if not waited:
            time.sleep(3)
        else:
            time.sleep(1)
    
    def _extract_html(self) -> str:
        """
        Extrae HTML completo de la página.
        El parser buscará el precio en JSON embebido (window.__PRELOADED_STATE__)
        o en HTML visible del sidebar de reserva.
        """
        return self.page.content()
