"""
SCRIPT DE PRUEBA: Generar URLs con diferentes formatos de parámetros
Para que el usuario pruebe manualmente cuál funciona
"""

from datetime import datetime

def generar_urls_test():
    """Genera múltiples variaciones de URL para probar"""
    
    url_base = "https://www.airbnb.es/rooms/1413234233737891700"
    checkin = datetime(2025, 12, 15)
    checkout = datetime(2025, 12, 18)
    
    print("\n" + "="*80)
    print("PRUEBA DE FORMATOS DE URL - Airbnb")
    print("="*80)
    print("\n📋 INSTRUCCIONES:")
    print("Copia cada URL en tu navegador y verifica si muestra el precio.")
    print("Anota cuál formato funciona correctamente.\n")
    
    formatos = [
        {
            "nombre": "Formato 1: check_in / check_out (guión bajo)",
            "url": f"{url_base}?check_in={checkin.strftime('%Y-%m-%d')}&check_out={checkout.strftime('%Y-%m-%d')}&adults=2"
        },
        {
            "nombre": "Formato 2: checkin / checkout (sin guión)",
            "url": f"{url_base}?checkin={checkin.strftime('%Y-%m-%d')}&checkout={checkout.strftime('%Y-%m-%d')}&adults=2"
        },
        {
            "nombre": "Formato 3: Con source_impression_id",
            "url": f"{url_base}?check_in={checkin.strftime('%Y-%m-%d')}&check_out={checkout.strftime('%Y-%m-%d')}&adults=2&source_impression_id=p3_test"
        },
        {
            "nombre": "Formato 4: Formato ISO completo",
            "url": f"{url_base}?check_in={checkin.isoformat()}&check_out={checkout.isoformat()}&adults=2"
        },
        {
            "nombre": "Formato 5: Con guión medio en fechas",
            "url": f"{url_base}?check_in={checkin.strftime('%Y-%m-%d')}&check_out={checkout.strftime('%Y-%m-%d')}&adults=2&children=0&infants=0"
        },
    ]
    
    for idx, formato in enumerate(formatos, 1):
        print(f"\n{'='*80}")
        print(f"{idx}. {formato['nombre']}")
        print(f"{'='*80}")
        print(f"URL: {formato['url']}")
        print()
    
    print("\n" + "="*80)
    print("📝 RESPONDE:")
    print("="*80)
    print("""
Formato que funciona: [número]
¿Muestra precio?: Sí/No
Precio visible: $_____ por noche
Screenshot: [opcional]

IMPORTANTE: Si NINGUNO funciona, necesito que hagas una búsqueda
manual desde airbnb.es y copies la URL completa resultante.
""")
    print("="*80)

if __name__ == "__main__":
    generar_urls_test()
