"""
Script de ejemplo para usar el monitor de precios desde línea de comandos
"""
import sys
import os
from datetime import datetime, timedelta

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.airbnb_scraper import AirbnbScraper
from src.booking_scraper import BookingScraper
from src.data_manager import DataManager


def main():
    print("💰 Price Monitor - Ejemplo de uso")
    print("=" * 50)
    
    # URLs de ejemplo
    airbnb_url = "https://www.airbnb.com.ar/rooms/928978094650118177"
    booking_url = "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"
    
    # Fechas
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    print(f"\nScrapeando precios desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
    print(f"Propiedad: Aizeder Eco Container House\n")
    
    # Inicializar scrapers
    airbnb = AirbnbScraper()
    booking = BookingScraper()
    data_manager = DataManager()
    
    results = []
    
    # Scrapear Airbnb
    print("🔍 Scrapeando Airbnb...")
    airbnb_results = airbnb.scrape_date_range(airbnb_url, start_date, end_date, nights=1, guests=2)
    results.extend(airbnb_results)
    
    print("\n🔍 Scrapeando Booking...")
    booking_results = booking.scrape_date_range(booking_url, start_date, end_date, nights=1, adults=2)
    results.extend(booking_results)
    
    # Guardar resultados
    print("\n💾 Guardando resultados...")
    data_manager.save_results(results, 'Aizeder Eco Container House')
    
    print("\n✅ Proceso completado!")
    print(f"Total de registros obtenidos: {len(results)}")
    
    # Mostrar estadísticas
    print("\n📊 Estadísticas:")
    stats = data_manager.get_summary_stats('Aizeder Eco Container House')
    if stats is not None:
        print(stats)


if __name__ == '__main__':
    main()
