"""
Scraper para obtener precios de Airbnb
"""
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import time
import os


class AirbnbScraper:
    def __init__(self):
        self.base_url = "https://www.airbnb.com.ar"
        self.debug_dir = 'debug'
        # Crear directorio debug si no existe
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def extract_room_id(self, url):
        """Extrae el ID del room de la URL de Airbnb"""
        match = re.search(r'/rooms/(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def build_url(self, room_id, checkin, checkout, guests=1):
        """Construye la URL con las fechas especificadas"""
        checkin_str = checkin.strftime('%Y-%m-%d')
        checkout_str = checkout.strftime('%Y-%m-%d')
        return f"{self.base_url}/rooms/{room_id}?check_in={checkin_str}&check_out={checkout_str}&guests={guests}&adults={guests}"
    
    def scrape_price(self, url, checkin_date, checkout_date, guests=1, debug=False, property_name='unknown'):
        """Extrae el precio de un listado de Airbnb"""
        room_id = self.extract_room_id(url)
        if not room_id:
            return None
            
        search_url = self.build_url(room_id, checkin_date, checkout_date, guests)
        
        try:
            with sync_playwright() as p:
                # Configurar navegador con anti-detección
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                # Crear contexto con configuración más realista
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='es-AR',
                    timezone_id='America/Argentina/Buenos_Aires'
                )
                
                # Inyectar script anti-detección
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = {
                        runtime: {}
                    };
                """)
                
                page = context.new_page()
                
                # Navegar con estrategia más simple
                print(f"  → Navegando a Airbnb...")
                page.goto(search_url, wait_until='domcontentloaded', timeout=90000)
                
                # Esperar un poco más para que cargue contenido dinámico
                print(f"  → Esperando carga de contenido...")
                time.sleep(8)
                
                # Intentar diferentes selectores para el precio
                price = None
                price_text = None
                found_selector = None
                
                # Selectores actualizados para Airbnb (2025)
                selectors = [
                    # Selectores de precio total
                    'div[data-section-id="BOOK_IT_SIDEBAR"] span[class*="_14y1gc"]',
                    'span._tyxjp1',
                    'span._1k4xcdh',
                    'div._1jo4hgw',
                    'span[class*="price"]',
                    'div[class*="PriceLockup"]',
                    'span[class*="_tyxjp1"]',
                    'div[class*="_1y74zjx"]',
                    # Selector más genérico
                    'span[aria-hidden="true"]',
                ]
                
                print(f"  → Buscando precio...")
                
                for selector in selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        for element in elements:
                            text = element.inner_text()
                            if text and ('$' in text or 'USD' in text) and any(char.isdigit() for char in text):
                                price_text = text
                                found_selector = selector
                                break
                        
                        if price_text:
                            break
                    except:
                        continue
                
                # Buscar también en todo el texto de la página
                if not price_text:
                    print(f"  → Buscando precio en texto de página...")
                    try:
                        page_text = page.inner_text('body')
                        
                        # PRIMERO: Detectar si está ocupado o no disponible
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
                        
                        is_unavailable = any(indicator in page_text for indicator in unavailable_indicators)
                        
                        if is_unavailable:
                            error_msg = "Alojamiento no disponible para estas fechas (posiblemente ocupado)"
                        else:
                            # Buscar patrones de precio en el texto
                            price_patterns = [
                                r'\$\s*([0-9,]+)\s*USD',
                                r'USD\s*\$?\s*([0-9,]+)',
                                r'\$([0-9,]+)\s*total',
                                r'Total\s*\$([0-9,]+)',
                            ]
                            
                            for pattern in price_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE)
                                if match:
                                    price_text = match.group(0)
                                    found_selector = f"regex:{pattern}"
                                    break
                    except:
                        pass
                
                # Si debug o no encontró precio, guardar info
                if debug or not price_text:
                    # Crear nombre de archivo único: propiedad + fecha + timestamp
                    timestamp = datetime.now().strftime("%H%M%S")
                    safe_property_name = re.sub(r'[^\w\s-]', '', property_name).strip().replace(' ', '_')[:30]
                    
                    screenshot_path = os.path.join(
                        self.debug_dir, 
                        f'airbnb_{safe_property_name}_{checkin_date.strftime("%Y%m%d")}_{timestamp}.png'
                    )
                    html_path = os.path.join(
                        self.debug_dir, 
                        f'airbnb_{safe_property_name}_{checkin_date.strftime("%Y%m%d")}_{timestamp}.html'
                    )
                    
                    page.screenshot(path=screenshot_path)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    print(f"  → Debug: Screenshot guardado en {screenshot_path}")
                    print(f"  → Debug: HTML guardado en {html_path}")
                
                if price_text:
                    # Extraer el número del precio
                    clean_text = price_text.replace(',', '').replace('.', '')
                    match = re.search(r'(\d+)', clean_text)
                    if match:
                        price = float(match.group(1))
                        print(f"  → Precio encontrado: ${price} USD (selector: {found_selector})")
                
                browser.close()
                
                if price:
                    return {
                        'platform': 'Airbnb',
                        'checkin': checkin_date.strftime('%Y-%m-%d'),
                        'checkout': checkout_date.strftime('%Y-%m-%d'),
                        'price_usd': price,
                        'guests': guests,
                        'scraped_at': datetime.now().isoformat(),
                        'url': search_url
                    }
                else:
                    # Diferenciar entre "no disponible" y "error de scraping"
                    error_message = error_msg if 'error_msg' in locals() else 'No se pudo extraer el precio'
                    print(f"  → {error_message}")
                    return {
                        'platform': 'Airbnb',
                        'checkin': checkin_date.strftime('%Y-%m-%d'),
                        'checkout': checkout_date.strftime('%Y-%m-%d'),
                        'price_usd': None,
                        'guests': guests,
                        'scraped_at': datetime.now().isoformat(),
                        'url': search_url,
                        'error': error_message
                    }
                    
        except Exception as e:
            print(f"  → Error: {str(e)}")
            return {
                'platform': 'Airbnb',
                'checkin': checkin_date.strftime('%Y-%m-%d'),
                'checkout': checkout_date.strftime('%Y-%m-%d'),
                'price_usd': None,
                'guests': guests,
                'scraped_at': datetime.now().isoformat(),
                'url': search_url,
                'error': str(e)
            }
    
    def scrape_date_range(self, url, start_date, end_date, nights=1, guests=1, debug_first=True, property_name='unknown'):
        """
        Obtiene precios para un rango de fechas
        
        Args:
            url: URL del alojamiento
            start_date: fecha de inicio (datetime)
            end_date: fecha de fin (datetime)
            nights: número de noches por reserva
            guests: número de huéspedes
            debug_first: si True, guarda debug info del primer scraping
            property_name: nombre de la propiedad (para archivos debug)
            
        Returns:
            list de dicts con precios para cada fecha
        """
        results = []
        current_date = start_date
        first_run = True
        
        while current_date <= end_date:
            checkout = current_date + timedelta(days=nights)
            
            print(f"  Scrapeando Airbnb: {current_date.strftime('%Y-%m-%d')} -> {checkout.strftime('%Y-%m-%d')}")
            
            # Debug solo en el primer scraping si se solicita
            debug = debug_first and first_run
            result = self.scrape_price(url, current_date, checkout, guests, debug=debug, property_name=property_name)
            if result:
                results.append(result)
            
            first_run = False
            
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
            
            # Pequeña pausa para no saturar el servidor
            time.sleep(2)
        
        return results
