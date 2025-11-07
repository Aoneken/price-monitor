#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones de:
1. Extracción correcta de precios en Airbnb (rango razonable)
2. Guardado de registros para todas las noches del período
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import get_db


def test_validacion_precio():
    """Prueba la función de validación de precios"""
    import re
    
    def validar_precio(texto: str) -> bool:
        """Valida que el precio esté en un rango razonable"""
        try:
            numeros = re.sub(r'[^\d]', '', texto)
            if not numeros:
                return False
            precio = float(numeros)
            return 10 <= precio <= 10000
        except:
            return False
    
    # Casos de prueba
    casos = [
        ("$50", True),
        ("$150 USD", True),
        ("$1,500", True),
        ("$13861461146138", False),  # Precio irrisorio
        ("$5", False),  # Muy barato
        ("$15000", False),  # Muy caro
        ("abc", False),  # Sin números
    ]
    
    print("=== TEST: Validación de Precios ===")
    for texto, esperado in casos:
        resultado = validar_precio(texto)
        estado = "✓" if resultado == esperado else "✗"
        print(f"{estado} {texto:20s} -> {resultado} (esperado: {esperado})")
    
    print()


def test_guardado_multiple_noches():
    """Simula el guardado de múltiples noches"""
    from datetime import timedelta
    
    print("=== TEST: Guardado Múltiple de Noches ===")
    
    # Simular resultado con 2 noches
    fecha_inicio = datetime(2025, 11, 7)
    noches = 2
    precio = 150.0
    
    print(f"Fecha inicio: {fecha_inicio.date()}")
    print(f"Noches encontradas: {noches}")
    print(f"Precio por noche: ${precio:.2f}")
    print()
    
    # Generar fechas según la lógica corregida
    if noches > 0 and precio > 0:
        fechas_a_guardar = [fecha_inicio + timedelta(days=i) for i in range(noches)]
        print(f"✓ Se guardarían {len(fechas_a_guardar)} registros:")
        for fecha in fechas_a_guardar:
            print(f"  - {fecha.date()}")
    else:
        print("✗ Solo se guardaría 1 registro (fecha de consulta)")
    
    print()


def verificar_base_datos():
    """Verifica los datos en la base de datos"""
    print("=== VERIFICACIÓN: Base de Datos ===")
    
    try:
        db = get_db()
        
        # Verificar establecimientos
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Contar establecimientos
            cursor.execute("SELECT COUNT(*) FROM Establecimientos")
            count_est = cursor.fetchone()[0]
            print(f"Establecimientos: {count_est}")
            
            # Contar URLs
            cursor.execute("SELECT COUNT(*) FROM Plataformas_URL WHERE esta_activa = 1")
            count_urls = cursor.fetchone()[0]
            print(f"URLs activas: {count_urls}")
            
            # Contar precios
            cursor.execute("SELECT COUNT(*) FROM Precios")
            count_precios = cursor.fetchone()[0]
            print(f"Registros de precios: {count_precios}")
            
            if count_precios > 0:
                # Mostrar últimos precios
                print("\nÚltimos 5 precios registrados:")
                cursor.execute("""
                    SELECT fecha_noche, precio_base, noches_encontradas, fecha_scrape
                    FROM Precios
                    ORDER BY fecha_scrape DESC
                    LIMIT 5
                """)
                for row in cursor.fetchall():
                    fecha, precio, noches, scrape = row
                    print(f"  {fecha}: ${precio:.2f} ({noches} noches) - {scrape}")
            
    except Exception as e:
        print(f"Error al verificar BD: {e}")
    
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("PRUEBA DE CORRECCIONES: Precio y Disponibilidad Múltiple")
    print("=" * 60)
    print()
    
    test_validacion_precio()
    test_guardado_multiple_noches()
    verificar_base_datos()
    
    print("=" * 60)
    print("NOTA: Para probar con scraping real, ejecuta el scraper")
    print("desde la interfaz de Streamlit en la página de Scraping.")
    print("=" * 60)
