"""
Script de prueba rápida con URL específica de Booking.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scheduler_v3 import ScraperScheduler


def test_booking_url():
    """Prueba con URL de Booking."""
    print("="*60)
    print("TEST RÁPIDO - Booking URL")
    print("="*60)
    
    # Inicializar scheduler
    scheduler = ScraperScheduler(
        cache_hours=0,  # Ignorar caché
        headless=True
    )
    
    # Obtener URLs
    urls = scheduler.get_urls_to_scrape()
    
    # Buscar primera URL de Booking
    booking_url = None
    for url in urls:
        if url['plataforma'].lower() == 'booking':
            booking_url = url
            break
    
    if not booking_url:
        print("❌ No hay URLs de Booking disponibles")
        return
    
    print(f"\n✓ URL de Booking encontrada")
    print(f"\n📍 Testing URL:")
    print(f"  Plataforma: {booking_url['plataforma']}")
    print(f"  URL: {booking_url['url']}")
    print(f"  ID: {booking_url['id_plataforma_url']}")
    
    # Fechas
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    
    print(f"\n📅 Búsqueda:")
    print(f"  Check-in: {check_in}")
    print(f"  Check-out: {check_out}")
    print(f"  Noches: 2")
    
    print(f"\n🤖 Iniciando scraping...")
    
    # Ejecutar scraping
    result = scheduler.scrape_url(booking_url, check_in, check_out)
    
    # Mostrar resultado
    print(f"\n" + "="*60)
    print("RESULTADO")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Plataforma: {result['platform']}")
    print(f"URL ID: {result['url_id']}")
    
    if result['status'] == 'success':
        print(f"✓ Noches guardadas: {result['nights_saved']}")
        print(f"✓ Estado BD: {result['save_status']}")
        if result.get('quote'):
            quote = result['quote']
            print(f"\n📊 Cotización:")
            print(f"  Precio total: {quote.get('precio_total')} {quote.get('moneda')}")
            print(f"  Disponibilidad: {quote.get('disponibilidad')}")
            print(f"  Noches: {len(quote.get('noches', []))}")
    else:
        print(f"✗ Error: {result['error']}")
    
    print("="*60)
    
    # Cleanup
    if scheduler.orchestrator:
        scheduler.orchestrator.cleanup()
    
    print("\n✓ Test completado")


if __name__ == '__main__':
    test_booking_url()
