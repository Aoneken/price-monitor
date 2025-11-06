"""
Scraper para obtener precios de Booking.com
"""
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import time
import os


class BookingScraper:
    def __init__(self):
        self.base_url = "https://www.booking.com"
        self.debug_dir = 'debug'
        # Crear directorio debug si no existe
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def extract_hotel_id(self, url):
        """Extrae el ID del hotel de la URL de Booking"""
        match = re.search(r'/hotel/[a-z]{2}/([^.?]+)', url)
        if match:
            return match.group(1)
        return None
    
    def build_url(self, hotel_slug, checkin, checkout, adults=2):
        """Construye la URL con las fechas especificadas"""
        checkin_str = checkin.strftime('%Y-%m-%d')
        checkout_str = checkout.strftime('%Y-%m-%d')
        
        # Buscar el país en la URL original si está disponible
        return f"{self.base_url}/hotel/ar/{hotel_slug}.es.html?checkin={checkin_str}&checkout={checkout_str}&group_adults={adults}&no_rooms=1&group_children=0"
    
    def scrape_price(self, url, checkin_date, checkout_date, adults=2, debug=False, property_name='unknown'):
        """
        Obtiene el precio para una fecha específica
        
        Args:
            url: URL del hotel en Booking
            checkin_date: datetime object para check-in
            checkout_date: datetime object para check-out
            adults: número de adultos
            debug: si True, guarda screenshot y HTML para debugging
            
        Returns:
            dict con información del precio o None si falla
        """
        hotel_slug = self.extract_hotel_id(url)
        if not hotel_slug:
            return None
            
        search_url = self.build_url(hotel_slug, checkin_date, checkout_date, adults)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                # Crear contexto con configuración más realista
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='es-AR'
                )
                
                page = context.new_page()
                
                # Navegar a la página
                page.goto(search_url, wait_until='networkidle', timeout=60000)
                
                # Esperar que cargue el contenido
                time.sleep(5)
                
                price = None
                price_text = None
                found_selector = None
                
                # Selectores actualizados para Booking (2025)
                selectors = [
                    '[data-testid="price-and-discounted-price"]',
                    'span[data-testid="price-for-x-nights"]',
                    'div[class*="prco-inline-block-maker-helper"]',
                    'span.prco-valign-middle-helper',
                    'span.prco-text-nowrap-helper',
                    'div.bui-price-display__value',
                    'span[aria-live="assertive"]',
                    # Buscar por patrón de texto
                    'text=/US\\$\\s*[0-9,]+/',
                    'text=/\\$\\s*[0-9,]+/',
                ]
                
                # Esperar por elementos de precio
                try:
                    page.wait_for_selector('[class*="price"], span[data-testid*="price"]', timeout=10000)
                except:
                    pass
                
                for selector in selectors:
                    try:
                        if selector.startswith('text='):
                            elements = page.locator(selector).all()
                            for element in elements:
                                text = element.inner_text()
                                if text and ('$' in text or 'USD' in text or 'US$' in text):
                                    price_text = text
                                    found_selector = selector
                                    break
                        else:
                            elements = page.query_selector_all(selector)
                            for element in elements:
                                text = element.inner_text()
                                if text and ('$' in text or 'USD' in text or 'US$' in text):
                                    price_text = text
                                    found_selector = selector
                                    break
                        
                        if price_text:
                            break
                    except:
                        continue
                
                # Si no encontró precio, verificar si está ocupado
                if not price_text:
                    try:
                        page_text = page.inner_text('body')
                        
                        # Detectar indicadores de no disponibilidad
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
                        
                        is_unavailable = any(indicator in page_text for indicator in unavailable_indicators)
                        
                        if is_unavailable:
                            error_msg = "Alojamiento no disponible para estas fechas (posiblemente ocupado)"
                    except:
                        pass
                
                # Si debug o no encontró precio, guardar info
                if debug or not price_text:
                    # Crear nombre de archivo único: propiedad + fecha + timestamp
                    timestamp = datetime.now().strftime("%H%M%S")
                    safe_property_name = re.sub(r'[^\w\s-]', '', property_name).strip().replace(' ', '_')[:30]
                    
                    screenshot_path = os.path.join(
                        self.debug_dir, 
                        f'booking_{safe_property_name}_{checkin_date.strftime("%Y%m%d")}_{timestamp}.png'
                    )
                    html_path = os.path.join(
                        self.debug_dir, 
                        f'booking_{safe_property_name}_{checkin_date.strftime("%Y%m%d")}_{timestamp}.html'
                    )
                    
                    page.screenshot(path=screenshot_path, full_page=True)
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    print(f"  → Debug: Screenshot guardado en {screenshot_path}")
                    print(f"  → Debug: HTML guardado en {html_path}")
                
                if price_text:
                    # Extraer el número del precio
                    # Limpiar y buscar el número
                    clean_text = price_text.replace('.', '').replace(',', '').replace('US', '').replace('$', '').strip()
                    match = re.search(r'(\d+)', clean_text)
                    if match:
                        price = float(match.group(1))
                        print(f"  → Precio encontrado: ${price} USD (selector: {found_selector})")
                
                browser.close()
                
                if price:
                    return {
                        'platform': 'Booking',
                        'checkin': checkin_date.strftime('%Y-%m-%d'),
                        'checkout': checkout_date.strftime('%Y-%m-%d'),
                        'price_usd': price,
                        'adults': adults,
                        'scraped_at': datetime.now().isoformat(),
                        'url': search_url
                    }
                else:
                    # Diferenciar entre "no disponible" y "error de scraping"
                    error_message = error_msg if 'error_msg' in locals() else 'No se pudo extraer el precio'
                    print(f"  → {error_message}")
                    return {
                        'platform': 'Booking',
                        'checkin': checkin_date.strftime('%Y-%m-%d'),
                        'checkout': checkout_date.strftime('%Y-%m-%d'),
                        'price_usd': None,
                        'adults': adults,
                        'scraped_at': datetime.now().isoformat(),
                        'url': search_url,
                        'error': error_message
                    }
                    
        except Exception as e:
            print(f"  → Error: {str(e)}")
            return {
                'platform': 'Booking',
                'checkin': checkin_date.strftime('%Y-%m-%d'),
                'checkout': checkout_date.strftime('%Y-%m-%d'),
                'price_usd': None,
                'adults': adults,
                'scraped_at': datetime.now().isoformat(),
                'url': search_url,
                'error': str(e)
            }
    
    def scrape_date_range(self, url, start_date, end_date, nights=1, adults=2, debug_first=True, property_name='unknown'):
        """
        Obtiene precios para un rango de fechas
        
        Args:
            url: URL del hotel
            start_date: fecha de inicio (datetime)
            end_date: fecha de fin (datetime)
            nights: número de noches por reserva
            adults: número de adultos
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
            
            print(f"  Scrapeando Booking: {current_date.strftime('%Y-%m-%d')} -> {checkout.strftime('%Y-%m-%d')}")
            
            # Debug solo en el primer scraping si se solicita
            debug = debug_first and first_run
            result = self.scrape_price(url, current_date, checkout, adults, debug=debug, property_name=property_name)
            if result:
                results.append(result)
            
            first_run = False
            
            # Avanzar al siguiente día
            current_date += timedelta(days=1)
            
            # Pausa para no saturar
            time.sleep(2)
        
        return results
