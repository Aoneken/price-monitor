"""
Orquestador V3 para scraping multi-plataforma.
"""
from datetime import date
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Browser
from src.robots.airbnb_robot import AirbnbRobotV3
from src.robots.booking_robot import BookingRobotV3
from src.robots.expedia_robot import ExpediaRobotV3


class OrchestratorV3:
    """
    Coordina el scraping de múltiples plataformas.
    
    Uso:
        orchestrator = OrchestratorV3(headless=True)
        results = orchestrator.scrape_all(establishments)
        orchestrator.cleanup()
    """
    
    def __init__(self, headless: bool = True):
        """
        Inicializa el orquestador.
        
        Args:
            headless: Modo headless de Playwright
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        
        # Mapeo de plataformas a robots
        self.robots = {}
    
    def _init_browser(self) -> None:
        """Inicializa Playwright y browser."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            
            # Instanciar robots
            self.robots = {
                'airbnb': AirbnbRobotV3(self.browser, self.headless),
                'booking': BookingRobotV3(self.browser, self.headless),
                'expedia': ExpediaRobotV3(self.browser, self.headless)
            }
    
    def scrape_establishment(
        self,
        platform: str,
        url: str,
        check_in: date,
        check_out: date,
        property_id: str
    ) -> Dict:
        """
        Scraping de un establecimiento.
        
        Args:
            platform: 'airbnb', 'booking', o 'expedia'
            url: URL del establecimiento
            check_in: Fecha check-in
            check_out: Fecha check-out
            property_id: ID de la propiedad
        
        Returns:
            Quote dict con resultado o error
        """
        self._init_browser()
        
        platform_lower = platform.lower()
        
        if platform_lower not in self.robots:
            return {
                'property_id': property_id,
                'platform': platform,
                'status': 'error',
                'error': f'Platform not supported: {platform}',
                'data': None
            }
        
        try:
            robot = self.robots[platform_lower]
            quote = robot.scrape(url, check_in, check_out, property_id)
            
            return {
                'property_id': property_id,
                'platform': platform,
                'status': 'success',
                'error': None,
                'data': quote
            }
        
        except Exception as e:
            return {
                'property_id': property_id,
                'platform': platform,
                'status': 'error',
                'error': str(e),
                'data': None
            }
    
    def scrape_all(
        self,
        establishments: List[Dict]
    ) -> List[Dict]:
        """
        Scraping de múltiples establecimientos.
        
        Args:
            establishments: Lista de dicts con:
                - platform: str
                - url: str
                - check_in: date
                - check_out: date
                - property_id: str
        
        Returns:
            Lista de resultados (success/error)
        """
        results = []
        
        for est in establishments:
            result = self.scrape_establishment(
                platform=est['platform'],
                url=est['url'],
                check_in=est['check_in'],
                check_out=est['check_out'],
                property_id=est['property_id']
            )
            results.append(result)
        
        return results
    
    def cleanup(self) -> None:
        """Limpieza de recursos de Playwright."""
        if self.robots:
            for robot in self.robots.values():
                robot.cleanup()
        
        if self.browser:
            self.browser.close()
        
        if self.playwright:
            self.playwright.stop()
