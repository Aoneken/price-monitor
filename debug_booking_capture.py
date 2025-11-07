"""
Script para capturar HTML y diagnosticar selectores de Booking.
"""
import asyncio
from datetime import date, timedelta
from pathlib import Path
from playwright.async_api import async_playwright


async def capture_booking_html():
    """Captura HTML de Booking para diagnóstico."""
    
    url_base = "https://www.booking.com/hotel/ar/viento-de-glaciares.es-ar.html"
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    
    # Construir URL con parámetros
    url = f"{url_base}?checkin={check_in}&checkout={check_out}&group_adults=1&no_rooms=1"
    
    print(f"🌐 URL: {url}")
    print(f"📅 Check-in: {check_in}, Check-out: {check_out}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"\n🤖 Navegando...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Esperar un poco más
            await page.wait_for_timeout(3000)
            
            # Capturar HTML
            html = await page.content()
            
            # Guardar HTML
            output_file = Path('debug') / f'booking_viento_{check_in.strftime("%Y%m%d")}.html'
            output_file.parent.mkdir(exist_ok=True)
            output_file.write_text(html, encoding='utf-8')
            
            print(f"✓ HTML guardado en: {output_file}")
            print(f"  Tamaño: {len(html)} bytes")
            
            # Buscar selectores de precio
            print(f"\n🔍 Buscando selectores de precio...")
            
            selectors = [
                "[data-testid*='price']",
                ".prco-valign-middle-helper",
                "[data-testid='price-and-discounted-price']",
                ".bui-price-display__value",
                ".prco-text-nowrap-helper",
                "span:has-text('ARS')",
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        print(f"  ✓ {selector}: '{text.strip()}'")
                    else:
                        print(f"  ✗ {selector}: No encontrado")
                except Exception as e:
                    print(f"  ✗ {selector}: Error - {e}")
            
            # Screenshot
            screenshot_file = Path('debug_screenshots') / f'booking_viento_{check_in.strftime("%Y%m%d")}.png'
            screenshot_file.parent.mkdir(exist_ok=True)
            await page.screenshot(path=str(screenshot_file), full_page=True)
            print(f"\n✓ Screenshot guardado en: {screenshot_file}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(capture_booking_html())
