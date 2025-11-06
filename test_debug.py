"""
Script de prueba rápida con debugging activado
"""
import sys
import os
from datetime import datetime, timedelta

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper


def test_single_scraping():
    print("🧪 Prueba Rápida de Scraping (CON DEBUG)")
    print("=" * 60)
    
    # URLs de ejemplo
    airbnb_url = "https://www.airbnb.com.ar/rooms/928978094650118177"
    booking_url = "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"
    
    # Una sola fecha para probar
    checkin = datetime(2025, 12, 15)
    checkout = datetime(2025, 12, 17)
    
    print(f"\n📅 Probando fecha: {checkin.strftime('%Y-%m-%d')} -> {checkout.strftime('%Y-%m-%d')}")
    print(f"Noches: 2 | Huéspedes: 2\n")
    
    # Test Airbnb
    print("=" * 60)
    print("🔍 PROBANDO AIRBNB")
    print("=" * 60)
    airbnb = AirbnbScraper()
    result_airbnb = airbnb.scrape_price(airbnb_url, checkin, checkout, guests=2, debug=True)
    
    print("\nResultado Airbnb:")
    print(f"  Precio: {result_airbnb.get('price_usd', 'NO ENCONTRADO')}")
    print(f"  URL: {result_airbnb.get('url', '')}")
    if 'error' in result_airbnb:
        print(f"  Error: {result_airbnb['error']}")
    
    print("\n" + "=" * 60)
    print("🔍 PROBANDO BOOKING")
    print("=" * 60)
    booking = BookingScraper()
    result_booking = booking.scrape_price(booking_url, checkin, checkout, adults=2, debug=True)
    
    print("\nResultado Booking:")
    print(f"  Precio: {result_booking.get('price_usd', 'NO ENCONTRADO')}")
    print(f"  URL: {result_booking.get('url', '')}")
    if 'error' in result_booking:
        print(f"  Error: {result_booking['error']}")
    
    print("\n" + "=" * 60)
    print("✅ Prueba completada")
    print("=" * 60)
    print("\nRevisa los archivos generados:")
    print("  - debug_airbnb_20251215.png")
    print("  - debug_airbnb_20251215.html")
    print("  - debug_booking_20251215.png")
    print("  - debug_booking_20251215.html")
    print("\nAbre el HTML en tu navegador para ver qué está viendo el scraper.")


if __name__ == '__main__':
    test_single_scraping()
