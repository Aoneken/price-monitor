"""
Utilidades para configurar navegadores con anti-detección (stealth mode)
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext
from typing import Optional
import random
from config.settings import SCRAPER_CONFIG, USER_AGENTS


def configurar_navegador_stealth() -> tuple[Browser, BrowserContext]:
    """
    Configura un navegador Playwright con técnicas anti-detección.
    
    Returns:
        Tupla (browser, context) lista para usar
    """
    playwright = sync_playwright().start()
    
    # Configuración de navegador para parecer humano
    browser = playwright.chromium.launch(
        headless=SCRAPER_CONFIG['headless'],
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
    )
    
    # User-Agent aleatorio
    user_agent = random.choice(USER_AGENTS)
    
    # Crear contexto con configuración realista
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=user_agent,
        locale='es-ES',
        timezone_id='Europe/Madrid',
        permissions=['geolocation'],
        geolocation={'latitude': 40.4168, 'longitude': -3.7038},  # Madrid
        color_scheme='light',
        device_scale_factor=1,
    )
    
    # Inyectar scripts anti-detección
    context.add_init_script("""
        // Ocultar webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Sobrescribir chrome object
        window.chrome = {
            runtime: {}
        };
        
        // Ocultar automation
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Ocultar headless
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-ES', 'es', 'en-US', 'en']
        });
    """)
    
    return browser, context


def get_random_user_agent() -> str:
    """Retorna un User-Agent aleatorio de la lista configurada"""
    return random.choice(USER_AGENTS)


def tomar_screenshot(page, nombre_archivo: str = "error.png"):
    """
    Toma un screenshot de la página actual para debugging.
    Útil cuando hay errores de scraping.
    
    Args:
        page: Página de Playwright
        nombre_archivo: Nombre del archivo de screenshot
    """
    try:
        from pathlib import Path
        screenshots_dir = Path(__file__).parent.parent.parent / 'logs' / 'screenshots'
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        screenshot_path = screenshots_dir / nombre_archivo
        page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    except Exception as e:
        print(f"Error tomando screenshot: {e}")
        return None
