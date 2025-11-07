"""
Demo del SDK V3 - Scraping de múltiples plataformas.

Uso:
    python demo_v3.py
"""
from datetime import date, timedelta
from src.orchestrator_v3 import OrchestratorV3
import json


def demo_single_platform():
    """Demo de scraping de una sola plataforma."""
    print("=== DEMO: Scraping de Airbnb ===\n")
    
    orchestrator = OrchestratorV3(headless=True)
    
    try:
        result = orchestrator.scrape_establishment(
            platform='airbnb',
            url='https://www.airbnb.com/rooms/12345',
            check_in=date.today() + timedelta(days=30),
            check_out=date.today() + timedelta(days=32),
            property_id='airbnb_12345'
        )
        
        print(f"Status: {result['status']}")
        print(f"Platform: {result['platform']}")
        
        if result['status'] == 'success':
            print("\nDatos extraídos:")
            print(json.dumps(result['data'], indent=2, default=str))
        else:
            print(f"\nError: {result['error']}")
    
    finally:
        orchestrator.cleanup()


def demo_multi_platform():
    """Demo de scraping de múltiples plataformas."""
    print("=== DEMO: Scraping Multi-Plataforma ===\n")
    
    check_in = date.today() + timedelta(days=30)
    check_out = date.today() + timedelta(days=32)
    
    establishments = [
        {
            'platform': 'airbnb',
            'url': 'https://www.airbnb.com/rooms/12345',
            'check_in': check_in,
            'check_out': check_out,
            'property_id': 'airbnb_12345'
        },
        {
            'platform': 'booking',
            'url': 'https://www.booking.com/hotel/ar/example.html',
            'check_in': check_in,
            'check_out': check_out,
            'property_id': 'booking_67890'
        },
        {
            'platform': 'expedia',
            'url': 'https://www.expedia.com/h12345',
            'check_in': check_in,
            'check_out': check_out,
            'property_id': 'expedia_abcde'
        }
    ]
    
    orchestrator = OrchestratorV3(headless=True)
    
    try:
        results = orchestrator.scrape_all(establishments)
        
        print(f"Establecimientos procesados: {len(results)}\n")
        
        for i, result in enumerate(results, 1):
            print(f"--- Establecimiento {i} ---")
            print(f"Platform: {result['platform']}")
            print(f"Property ID: {result['property_id']}")
            print(f"Status: {result['status']}")
            
            if result['status'] == 'success':
                data = result['data']
                print(f"Precio total: {data.get('precio_total_vigente', data.get('precio_total', 'N/A'))}")
                print(f"Precio por noche: {data.get('precio_por_noche', 'N/A')}")
                print(f"Noches: {data.get('nights', 'N/A')}")
                print(f"WiFi: {data.get('wifi_incluido', 'N/A')}")
                print(f"Desayuno: {data.get('incluye_desayuno', 'N/A')}")
                print(f"Quality: {data.get('quality', 'N/A')}")
            else:
                print(f"Error: {result['error']}")
            
            print()
    
    finally:
        orchestrator.cleanup()


def demo_parsers_only():
    """Demo de parsers sin navegación (con HTML de ejemplo)."""
    print("=== DEMO: Parsers con HTML de ejemplo ===\n")
    
    from src.parsers.airbnb_parser import AirbnbParser
    from src.parsers.booking_parser import BookingParser
    from src.parsers.expedia_parser import ExpediaParser
    
    check_in = date.today() + timedelta(days=30)
    check_out = date.today() + timedelta(days=32)
    
    # Airbnb
    print("--- Airbnb Parser ---")
    airbnb_html = """
    <div data-testid="price-item-total">$665,03 USD en total por 2 noches</div>
    <div>WiFi disponible</div>
    <div>Desayuno incluido</div>
    """
    
    try:
        airbnb_quote = AirbnbParser.build_quote(
            property_id='airbnb_test',
            html=airbnb_html,
            check_in=check_in,
            check_out=check_out,
            fuente='dom'
        )
        print(f"Precio total: ${airbnb_quote['precio_total']}")
        print(f"Precio por noche: ${airbnb_quote['precio_por_noche']}")
        print(f"WiFi: {airbnb_quote['wifi_incluido']}")
        print(f"Desayuno: {airbnb_quote['incluye_desayuno']}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Booking
    print("--- Booking Parser ---")
    booking_html = """
    <div class="price">US$500 por 2 noches</div>
    <div class="taxes">+ US$147 de impuestos y cargos</div>
    <div>WiFi gratis disponible</div>
    <div>Desayuno incluido en la tarifa</div>
    """
    
    try:
        booking_quote = BookingParser.build_quote(
            property_id='booking_test',
            html=booking_html,
            check_in=check_in,
            check_out=check_out,
            fuente='dom'
        )
        print(f"Precio total: ${booking_quote['precio_total']}")
        print(f"Precio por noche: ${booking_quote['precio_por_noche']}")
        print(f"Impuestos: ${booking_quote.get('impuestos_cargos_extra', 0)}")
        print(f"WiFi: {booking_quote['wifi_incluido']}")
        print(f"Desayuno: {booking_quote['incluye_desayuno']}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Expedia
    print("--- Expedia Parser ---")
    expedia_html = """
    <div><del>$562</del></div>
    <div>$505 en total</div>
    <div>$56 de dto.</div>
    <div>$253 por noche</div>
    <div>WiFi disponible</div>
    """
    
    try:
        expedia_quote = ExpediaParser.build_quote(
            property_id='expedia_test',
            html=expedia_html,
            check_in=check_in,
            check_out=check_out,
            fuente='dom'
        )
        print(f"Precio vigente: ${expedia_quote['precio_total_vigente']}")
        print(f"Precio original: ${expedia_quote.get('precio_original_tachado', 'N/A')}")
        print(f"Descuento: ${expedia_quote.get('monto_descuento', 0)} ({expedia_quote.get('porcentaje_descuento', 0)}%)")
        print(f"Precio por noche: ${expedia_quote['precio_por_noche']}")
        print(f"WiFi: {expedia_quote['wifi_incluido']}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == '__main__':
    import sys
    
    print("SDK V3 - Price Monitor\n")
    print("Opciones:")
    print("1. Demo parsers (sin navegación)")
    print("2. Demo scraping single platform (requiere URLs reales)")
    print("3. Demo scraping multi-platform (requiere URLs reales)")
    print()
    
    opcion = input("Selecciona opción [1-3]: ").strip()
    
    if opcion == '1':
        demo_parsers_only()
    elif opcion == '2':
        demo_single_platform()
    elif opcion == '3':
        demo_multi_platform()
    else:
        print("Opción inválida")
        sys.exit(1)
