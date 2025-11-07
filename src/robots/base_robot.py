"""
Robot base abstracto para scraping.
Define la interfaz común para todos los robots específicos de plataforma.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from playwright.sync_api import Page, Browser


class BaseRobot(ABC):
    """
    Clase base abstracta para robots de scraping.
    
    Todos los robots deben implementar:
    - scrape(): Método principal de scraping
    - _navigate(): Navegación específica de la plataforma
    - _extract_html(): Extracción del HTML relevante
    """
    
    def __init__(self, browser: Browser, headless: bool = True):
        """
        Inicializa el robot.
        
        Args:
            browser: Instancia de Playwright Browser
            headless: Modo headless
        """
        self.browser = browser
        self.headless = headless
        self.page: Optional[Page] = None
    
    @abstractmethod
    def scrape(
        self,
        url: str,
        check_in: date,
        check_out: date,
        property_id: str
    ) -> dict:
        """
        Scraping completo de la plataforma.
        
        Args:
            url: URL del establecimiento
            check_in: Fecha check-in
            check_out: Fecha check-out
            property_id: ID de la propiedad
        
        Returns:
            Quote dict según contrato de la plataforma
        
        Raises:
            ValueError: Error de extracción
            TimeoutError: Timeout navegación
        """
        pass
    
    @abstractmethod
    def _navigate(
        self,
        url: str,
        check_in: date,
        check_out: date
    ) -> None:
        """
        Navegación específica de la plataforma.
        
        Args:
            url: URL del establecimiento
            check_in: Fecha check-in
            check_out: Fecha check-out
        """
        pass
    
    @abstractmethod
    def _extract_html(self) -> str:
        """
        Extrae HTML relevante de la página.
        
        Returns:
            HTML con información de precios/amenities
        """
        pass
    
    def _init_page(self) -> Page:
        """
        Inicializa una nueva página con configuración stealth.
        
        Returns:
            Page configurada
        """
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Configuración stealth básica
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return page
    
    def _close_page(self) -> None:
        """Cierra la página actual."""
        if self.page:
            self.page.context.close()
            self.page = None
    
    def cleanup(self) -> None:
        """Limpieza de recursos."""
        self._close_page()
