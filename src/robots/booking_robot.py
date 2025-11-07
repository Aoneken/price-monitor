"""
Robot Booking V3 con Playwright.
"""
import time
from datetime import date
from playwright.sync_api import Browser
from src.robots.base_robot import BaseRobot
from src.parsers.booking_parser import BookingParser


class BookingRobotV3(BaseRobot):
    """
    Robot para scraping de Booking.
    
    Flujo:
    1. Navegar a URL con fechas
    2. Verificar fechas correctas
    3. Seleccionar cantidad de habitaciones (1)
    4. Esperar resumen de precios
    5. Extraer HTML del resumen
    6. Parsear con BookingParser
    """
    
    def __init__(self, browser: Browser, headless: bool = True):
        super().__init__(browser, headless)
        self.parser = BookingParser()
    
    def scrape(
        self,
        url: str,
        check_in: date,
        check_out: date,
        property_id: str
    ) -> dict:
        """
        Scraping completo de Booking.
        
        Returns:
            BookingQuote dict
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
        Navega a Booking con fechas y selecciona habitación.
        """
        # Construir URL con fechas
        base_url = url.split('?')[0]
        check_in_str = check_in.strftime('%Y-%m-%d')
        check_out_str = check_out.strftime('%Y-%m-%d')
        
        full_url = f"{base_url}?checkin={check_in_str}&checkout={check_out_str}&group_adults=1&no_rooms=1"
        
        # Navegar
        self.page.goto(full_url, wait_until='networkidle', timeout=30000)
        
        # Esperar disponibilidad de habitaciones
        self.page.wait_for_selector('[data-testid*="price"], .prco-valign-middle-helper', timeout=10000)
        
        time.sleep(1)
        
        # Intentar seleccionar habitación si hay selector
        try:
            room_select = self.page.query_selector('select[name="nr_rooms_"]')
            if room_select:
                room_select.select_option('1')
                time.sleep(0.5)
        except Exception:
            pass  # Ya está seleccionada o no hay selector
    
    def _extract_html(self) -> str:
        """
        Extrae HTML completo de la página.
        El parser buscará el precio en JSON embebido o en HTML visible.
        """
        return self.page.content()
