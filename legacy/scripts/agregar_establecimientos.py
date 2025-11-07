"""
Script para agregar establecimientos con múltiples URLs de forma masiva
Soporta Booking, Airbnb y Expedia
"""
import sys
from database.db_manager import get_db
import re

def detectar_plataforma(url: str) -> str:
    """Detecta la plataforma según la URL"""
    url_lower = url.lower()
    
    if 'booking.com' in url_lower:
        return 'Booking'
    elif 'airbnb' in url_lower:
        return 'Airbnb'
    elif 'expedia' in url_lower:
        return 'Expedia'
    else:
        return 'Desconocida'

def validar_url(url: str) -> bool:
    """Valida que la URL sea válida"""
    patron = r'^https?://(www\.)?([a-zA-Z0-9-]+\.)+(com|es|ar|mx|cl|co|pe|br)'
    return bool(re.match(patron, url))

def agregar_establecimiento(nombre: str, urls: list):
    """
    Agrega un establecimiento con sus URLs
    
    Args:
        nombre: Nombre del establecimiento
        urls: Lista de URLs (strings)
    """
    db = get_db()
    
    print(f"\n{'='*80}")
    print(f"AGREGANDO ESTABLECIMIENTO: {nombre}")
    print(f"{'='*80}\n")
    
    # Validar URLs
    urls_validas = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
            
        plataforma = detectar_plataforma(url)
        if plataforma == 'Desconocida':
            print(f"⚠️  URL no reconocida (se omitirá): {url[:60]}...")
            continue
        
        if not validar_url(url):
            print(f"⚠️  URL inválida (se omitirá): {url[:60]}...")
            continue
        
        urls_validas.append((url, plataforma))
    
    if not urls_validas:
        print("❌ No hay URLs válidas para agregar")
        return None
    
    print(f"URLs válidas detectadas: {len(urls_validas)}")
    for url, plataforma in urls_validas:
        print(f"  • {plataforma}: {url[:60]}...")
    
    # Confirmar
    respuesta = input(f"\n¿Deseas crear el establecimiento '{nombre}'? (s/n): ")
    if respuesta.lower() != 's':
        print("❌ Cancelado por el usuario")
        return None
    
    try:
        # Crear establecimiento
        id_establecimiento = db.create_establecimiento(nombre)
        print(f"✅ Establecimiento creado con ID: {id_establecimiento}")
        
        # Agregar URLs
        urls_agregadas = 0
        for url, plataforma in urls_validas:
            try:
                id_url = db.create_plataforma_url(id_establecimiento, plataforma, url)
                print(f"   ✅ URL agregada [{plataforma}]: ID {id_url}")
                urls_agregadas += 1
            except Exception as e:
                print(f"   ❌ Error agregando URL [{plataforma}]: {e}")
        
        print(f"\n✅ COMPLETADO: {urls_agregadas}/{len(urls_validas)} URLs agregadas exitosamente")
        return id_establecimiento
        
    except Exception as e:
        print(f"❌ Error creando establecimiento: {e}")
        return None

def agregar_multiples_establecimientos(datos: list):
    """
    Agrega múltiples establecimientos desde una lista
    
    Args:
        datos: Lista de tuplas (nombre, [urls])
    """
    print(f"\n{'='*80}")
    print(f"AGREGANDO MÚLTIPLES ESTABLECIMIENTOS")
    print(f"Total a agregar: {len(datos)}")
    print(f"{'='*80}\n")
    
    exitosos = 0
    for nombre, urls in datos:
        resultado = agregar_establecimiento(nombre, urls)
        if resultado:
            exitosos += 1
        print()  # Línea en blanco entre establecimientos
    
    print(f"\n{'='*80}")
    print(f"RESUMEN FINAL")
    print(f"Exitosos: {exitosos}/{len(datos)}")
    print(f"{'='*80}\n")

def modo_interactivo():
    """Modo interactivo para agregar un establecimiento"""
    print("\n" + "="*80)
    print("MODO INTERACTIVO - AGREGAR ESTABLECIMIENTO")
    print("="*80 + "\n")
    
    nombre = input("Nombre del establecimiento: ").strip()
    if not nombre:
        print("❌ Nombre vacío, cancelando...")
        return
    
    print("\nAhora ingresa las URLs (una por línea).")
    print("Presiona Enter sin texto para terminar.\n")
    
    urls = []
    contador = 1
    while True:
        url = input(f"URL {contador} (o Enter para terminar): ").strip()
        if not url:
            break
        urls.append(url)
        contador += 1
    
    if not urls:
        print("❌ No se ingresaron URLs, cancelando...")
        return
    
    agregar_establecimiento(nombre, urls)

def modo_batch():
    """Modo batch para agregar desde un archivo"""
    print("\n" + "="*80)
    print("MODO BATCH - AGREGAR DESDE ARCHIVO")
    print("="*80 + "\n")
    
    print("Formato del archivo:")
    print("  Nombre del Establecimiento 1")
    print("  https://booking.com/...")
    print("  https://airbnb.com/...")
    print("  ---")
    print("  Nombre del Establecimiento 2")
    print("  https://booking.com/...")
    print("  ---")
    print()
    
    archivo = input("Ruta del archivo: ").strip()
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Parsear contenido
        bloques = contenido.split('---')
        datos = []
        
        for bloque in bloques:
            lineas = [l.strip() for l in bloque.strip().split('\n') if l.strip()]
            if not lineas:
                continue
            
            nombre = lineas[0]
            urls = lineas[1:]
            
            if nombre and urls:
                datos.append((nombre, urls))
        
        if not datos:
            print("❌ No se encontraron datos válidos en el archivo")
            return
        
        print(f"\nSe encontraron {len(datos)} establecimientos en el archivo")
        agregar_multiples_establecimientos(datos)
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {archivo}")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")

def main():
    """Función principal"""
    print("\n🏨 SCRIPT DE AGREGAR ESTABLECIMIENTOS")
    print("="*80)
    
    print("\nOpciones:")
    print("  1. Modo interactivo (un establecimiento)")
    print("  2. Modo batch (múltiples desde archivo)")
    print("  3. Salir")
    
    opcion = input("\nSelecciona una opción: ").strip()
    
    if opcion == '1':
        modo_interactivo()
    elif opcion == '2':
        modo_batch()
    elif opcion == '3':
        print("👋 Saliendo...")
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main()
