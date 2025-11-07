"""
Script de prueba rápida del scheduler V3.
Ejecuta scraping de solo 1 URL para verificar funcionamiento.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scheduler_v3 import ScraperScheduler


def test_single_url():
    """Prueba con una sola URL."""
    print("="*60)
    print("TEST RÁPIDO - Scheduler V3")
    print("="*60)
    
    # Inicializar scheduler
    scheduler = ScraperScheduler(
        cache_hours=0,  # Ignorar caché
        headless=True
    )
    
    # Obtener URLs
    urls = scheduler.get_urls_to_scrape()
    
    if not urls:
        print("❌ No hay URLs disponibles en la BD")
        return
    
    print(f"\n✓ {len(urls)} URLs disponibles")
    
    # Tomar la primera URL
    test_url = urls[0]
    print(f"\n📍 Testing URL:")
    print(f"  Plataforma: {test_url['plataforma']}")
    print(f"  URL: {test_url['url'][:60]}...")
    print(f"  ID: {test_url['id_plataforma_url']}")
    
    # Fechas
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    
    print(f"\n📅 Búsqueda:")
    print(f"  Check-in: {check_in}")
    print(f"  Check-out: {check_out}")
    print(f"  Noches: 2")
    
    print(f"\n🤖 Iniciando scraping...")
    
    # Ejecutar scraping
    result = scheduler.scrape_url(test_url, check_in, check_out)
    
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
    else:
        print(f"✗ Error: {result['error']}")
    
    print("="*60)
    
    # Cleanup
    if scheduler.orchestrator:
        scheduler.orchestrator.cleanup()
    
    print("\n✓ Test completado")


if __name__ == '__main__':
    test_single_url()
