"""
Test básico para verificar que los módulos funcionan correctamente
"""
import sys
import os
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager
from src.visualizer import PriceVisualizer


def test_airbnb_scraper():
    """Test de inicialización del scraper de Airbnb"""
    scraper = AirbnbScraper()
    
    # Test de extracción de ID
    url = "https://www.airbnb.com.ar/rooms/928978094650118177"
    room_id = scraper.extract_room_id(url)
    
    assert room_id == "928978094650118177", f"Expected '928978094650118177', got '{room_id}'"
    print("✓ Test Airbnb scraper - extracción de ID: PASÓ")
    
    # Test de construcción de URL
    checkin = datetime(2025, 11, 10)
    checkout = datetime(2025, 11, 12)
    url = scraper.build_url(room_id, checkin, checkout, guests=2)
    
    assert "check_in=2025-11-10" in url, "URL debe contener fecha de check-in"
    assert "check_out=2025-11-12" in url, "URL debe contener fecha de check-out"
    print("✓ Test Airbnb scraper - construcción de URL: PASÓ")


def test_booking_scraper():
    """Test de inicialización del scraper de Booking"""
    scraper = BookingScraper()
    
    # Test de extracción de ID
    url = "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"
    hotel_id = scraper.extract_hotel_id(url)
    
    assert hotel_id == "aizeder-eco-container-house", f"Expected 'aizeder-eco-container-house', got '{hotel_id}'"
    print("✓ Test Booking scraper - extracción de ID: PASÓ")
    
    # Test de construcción de URL
    checkin = datetime(2025, 11, 10)
    checkout = datetime(2025, 11, 12)
    url = scraper.build_url(hotel_id, checkin, checkout, adults=2)
    
    assert "checkin=2025-11-10" in url, "URL debe contener fecha de check-in"
    assert "checkout=2025-11-12" in url, "URL debe contener fecha de check-out"
    print("✓ Test Booking scraper - construcción de URL: PASÓ")


def test_data_manager():
    """Test del gestor de datos"""
    dm = DataManager(data_dir='test_data')
    
    # Test de inicialización
    assert dm.data_dir == 'test_data', "Directorio de datos incorrecto"
    print("✓ Test Data Manager - inicialización: PASÓ")
    
    # Limpiar
    import shutil
    if os.path.exists('test_data'):
        shutil.rmtree('test_data')


def test_visualizer():
    """Test del visualizador"""
    viz = PriceVisualizer()
    
    # Test de inicialización
    assert 'Airbnb' in viz.colors, "Debe tener color para Airbnb"
    assert 'Booking' in viz.colors, "Debe tener color para Booking"
    print("✓ Test Visualizer - inicialización: PASÓ")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n🧪 Ejecutando tests...\n")
    print("=" * 50)
    
    try:
        test_airbnb_scraper()
        test_booking_scraper()
        test_data_manager()
        test_visualizer()
        
        print("=" * 50)
        print("\n✅ Todos los tests pasaron correctamente!\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test falló: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
