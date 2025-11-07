"""
Robot Expedia V3 con Playwright.
"""
import time
from datetime import date
from playwright.sync_api import Browser
from src.robots.base_robot import BaseRobot
from src.parsers.expedia_parser import ExpediaParser


class ExpediaRobotV3(BaseRobot):
    """
    Robot para scraping de Expedia.
    
    Flujo:
    1. Navegar a URL con fechas
    2. Scroll hasta la sticky card de precios
    3. Esperar carga completa
    4. Extraer HTML de la sticky card
    5. Parsear con ExpediaParser
    """
    
    def __init__(self, browser: Browser, headless: bool = True):
        super().__init__(browser, headless)
        self.parser = ExpediaParser()
    
    def scrape(
        self,
        url: str,
        check_in: date,
        check_out: date,
        property_id: str
    ) -> dict:
        """
        Scraping completo de Expedia.
        
        Returns:
            ExpediaQuote dict
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
        Navega a Expedia con fechas seleccionadas.
        """
        # Construir URL con fechas
        base_url = url.split('?')[0]
        check_in_str = check_in.strftime('%Y-%m-%d')
        check_out_str = check_out.strftime('%Y-%m-%d')
        
        full_url = f"{base_url}?chkin={check_in_str}&chkout={check_out_str}&adults=1"
        
        # Navegar
        self.page.goto(full_url, wait_until='networkidle', timeout=30000)
        
        # Esperar sticky card de precios
        self.page.wait_for_selector('[data-stid*="price"], .uitk-price-lockup', timeout=10000)
        
        time.sleep(1)
        
        # Scroll hasta la sticky card (suele estar abajo)
        try:
            sticky_card = self.page.query_selector('.uitk-card-roundcorner-all, [data-stid="property-offer"]')
            if sticky_card:
                sticky_card.scroll_into_view_if_needed()
                time.sleep(0.5)
        except Exception:
            pass  # Ya está visible
    
    def _extract_html(self) -> str:
        """
        Extrae HTML completo de la página.
        El parser buscará el precio en JSON embebido o en HTML visible
        de la sticky card de precios.
        """
        return self.page.content()
