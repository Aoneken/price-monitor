"""
Script para validar y agregar los establecimientos de la matriz
"""
import sys
sys.path.insert(0, '/workspaces/price-monitor')

from database.db_manager import get_db
import re

# Datos de la matriz
establecimientos_data = [
    {
        "nombre": "Patagonia Eco Domes",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/patagonia-eco-domes.es.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/20754903"),
            ("Expedia", "https://www.expedia.com.ar/El-Chalten-Hoteles-Patagonia-Eco-Domes.h10412487.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Cerro Eléctrico",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/cerro-electrico.es.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/39250879"),
            ("Expedia", "https://www.expedia.com/es/El-Chalten-Hoteles-Cerro-Electrico-Upcycled-Eco-Stay.h44319390.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Puesto Cagliero",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/puesto-cagliero-en-estancia-los-huemules.es.html"),
            ("Expedia", "https://www.expedia.com/es/El-Chalten-Hoteles-Puesto-Cagliero-En-Estancia-Los-Huemules.h21347332.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Estancia Bonanza",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/estancia-bonanza.es.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/47899064"),
            ("Expedia", "https://www.expedia.com/es/El-Chalten-Hoteles-Estancia-Bonanza.h96068230.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Bonanza Glamp Nature Experience",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/bonanza-glamp-nature-experience.es.html"),
            ("Expedia", "https://www.expedia.com/es/El-Chalten-Hoteles-Bonanza-Glamp-Nature-Experience.h119278520.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Viento de Glaciares",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/viento-de-glaciares.es-ar.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/1413234233737891700"),
            ("Expedia", "https://www.expedia.com/es/El-Chalten-Hoteles-Viento-De-Glaciares.h121342732.Informacion-Hotel"),
        ]
    },
    {
        "nombre": "Refugio Don Salvador",
        "urls": [
            ("Airbnb", "https://www.airbnb.com.ar/rooms/984157675633929889"),
            ("Expedia", "https://www.expedia.com.ar/Refugio-Don-Salvador-Tiny-House.h109439577"),
        ]
    },
    {
        "nombre": "Aizeder",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/928978094650118177"),
        ]
    },
    {
        "nombre": "Río Blanco (Casa en el bosque)",
        "urls": [
            ("Airbnb", "https://www.airbnb.com.ar/rooms/1529744827088402632"),
        ]
    },
    {
        "nombre": "Casa Negra",
        "urls": [
            ("Airbnb", "https://www.airbnb.com.ar/rooms/1036148891155939637"),
        ]
    },
    {
        "nombre": "El Pilar",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/el-pilar.es.html"),
        ]
    },
    {
        "nombre": "Camping Bonanza",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/bonanza-eco-aventura-camping.es.html"),
        ]
    },
    {
        "nombre": "OVO Patagonia",
        "urls": [
            ("Booking", "https://www.booking.com/hotel/ar/ovo-patagonia.es.html"),
            ("Airbnb", "https://www.airbnb.com.ar/rooms/1312689251939122522"),
        ]
    },
]

def validar_url(url: str, plataforma: str) -> tuple[bool, str]:
    """Valida que la URL sea correcta para la plataforma"""
    url_lower = url.lower()
    
    if plataforma == "Booking" and "booking.com" not in url_lower:
        return False, f"URL no parece ser de Booking: {url}"
    
    if plataforma == "Airbnb" and "airbnb" not in url_lower:
        return False, f"URL no parece ser de Airbnb: {url}"
    
    if plataforma == "Expedia" and "expedia" not in url_lower:
        return False, f"URL no parece ser de Expedia: {url}"
    
    # Validar formato básico de URL
    patron = r'^https?://'
    if not re.match(patron, url):
        return False, f"URL no tiene formato válido: {url}"
    
    return True, "OK"

def agregar_establecimientos():
    """Agrega todos los establecimientos a la base de datos"""
    db = get_db()
    
    print("\n" + "="*80)
    print("VALIDACIÓN Y AGREGADO DE ESTABLECIMIENTOS")
    print("="*80 + "\n")
    
    # Fase 1: Validación
    print("📋 FASE 1: VALIDACIÓN DE URLS")
    print("-" * 80)
    
    errores = []
    total_urls = 0
    
    for est in establecimientos_data:
        print(f"\n✓ {est['nombre']}")
        for plataforma, url in est['urls']:
            total_urls += 1
            valido, mensaje = validar_url(url, plataforma)
            if valido:
                print(f"  ✓ {plataforma}: OK")
            else:
                print(f"  ✗ {plataforma}: {mensaje}")
                errores.append(mensaje)
    
    if errores:
        print(f"\n❌ Se encontraron {len(errores)} errores en la validación:")
        for error in errores:
            print(f"  - {error}")
        print("\n⚠️  Corrija los errores antes de continuar")
        return
    
    print(f"\n✅ Validación exitosa: {total_urls} URLs válidas")
    
    # Fase 2: Confirmación
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    print(f"Total de establecimientos: {len(establecimientos_data)}")
    print(f"Total de URLs: {total_urls}")
    
    # Distribución por plataforma
    booking_count = sum(1 for est in establecimientos_data for p, u in est['urls'] if p == "Booking")
    airbnb_count = sum(1 for est in establecimientos_data for p, u in est['urls'] if p == "Airbnb")
    expedia_count = sum(1 for est in establecimientos_data for p, u in est['urls'] if p == "Expedia")
    
    print(f"\nDistribución por plataforma:")
    print(f"  • Booking: {booking_count} URLs")
    print(f"  • Airbnb: {airbnb_count} URLs")
    print(f"  • Expedia: {expedia_count} URLs")
    
    respuesta = input("\n¿Deseas proceder con el agregado? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Operación cancelada por el usuario")
        return
    
    # Fase 3: Agregado
    print("\n" + "="*80)
    print("📥 FASE 2: AGREGANDO A LA BASE DE DATOS")
    print("="*80 + "\n")
    
    exitosos = 0
    fallidos = 0
    
    for est in establecimientos_data:
        print(f"\n🏨 Agregando: {est['nombre']}")
        
        try:
            # Crear establecimiento
            id_est = db.create_establecimiento(est['nombre'])
            print(f"   ✓ Establecimiento creado con ID: {id_est}")
            
            # Agregar URLs
            urls_agregadas = 0
            for plataforma, url in est['urls']:
                try:
                    id_url = db.create_plataforma_url(id_est, plataforma, url)
                    print(f"   ✓ URL agregada [{plataforma}]: ID {id_url}")
                    urls_agregadas += 1
                except Exception as e:
                    print(f"   ✗ Error agregando URL [{plataforma}]: {e}")
                    fallidos += 1
            
            if urls_agregadas > 0:
                exitosos += 1
                print(f"   ✅ Completado: {urls_agregadas}/{len(est['urls'])} URLs")
        
        except Exception as e:
            print(f"   ❌ Error creando establecimiento: {e}")
            fallidos += 1
    
    # Resumen final
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print(f"Establecimientos agregados exitosamente: {exitosos}/{len(establecimientos_data)}")
    print(f"Errores: {fallidos}")
    
    if exitosos == len(establecimientos_data):
        print("\n🎉 ¡Todos los establecimientos fueron agregados exitosamente!")
    elif exitosos > 0:
        print(f"\n⚠️  {exitosos} establecimientos agregados, {fallidos} con errores")
    else:
        print("\n❌ No se pudo agregar ningún establecimiento")

if __name__ == "__main__":
    agregar_establecimientos()
