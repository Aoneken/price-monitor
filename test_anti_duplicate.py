"""
Script de prueba para verificar el sistema anti-duplicado de 48 horas
"""
import sys
import os
from datetime import datetime, timedelta

# Configurar path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_manager import DataManager

def test_anti_duplicate():
    """Prueba el sistema de detección de ejecuciones duplicadas"""
    
    dm = DataManager()
    
    print("=" * 60)
    print("PRUEBA: Sistema Anti-Duplicado (48 horas)")
    print("=" * 60)
    
    # Configuración de prueba
    property_name = "Test Property"
    start_date = datetime.now().date()
    end_date = (datetime.now() + timedelta(days=7)).date()
    nights = 2
    guests = 2
    platforms = ['airbnb', 'booking']
    
    print(f"\n✅ Configuración de prueba:")
    print(f"   - Propiedad: {property_name}")
    print(f"   - Fechas: {start_date} → {end_date}")
    print(f"   - Noches: {nights}")
    print(f"   - Huéspedes: {guests}")
    print(f"   - Plataformas: {platforms}")
    
    # Test 1: No debería haber ejecución reciente
    print(f"\n📋 Test 1: Verificar que NO hay ejecución reciente...")
    is_recent = dm.is_recent_same_run(
        property_name=property_name,
        start_date=start_date,
        end_date=end_date,
        nights=nights,
        guests=guests,
        platforms=platforms
    )
    
    if not is_recent:
        print("   ✅ PASS: No se encontró ejecución reciente")
    else:
        print("   ❌ FAIL: Se encontró ejecución reciente inesperada")
        return False
    
    # Test 2: Registrar una ejecución
    print(f"\n📋 Test 2: Registrar nueva ejecución...")
    record = dm.log_scrape_run(
        property_name=property_name,
        start_date=start_date,
        end_date=end_date,
        nights=nights,
        guests=guests,
        platforms=platforms
    )
    print(f"   ✅ PASS: Ejecución registrada con timestamp: {record['ts']}")
    
    # Test 3: Ahora SÍ debería detectar duplicado
    print(f"\n📋 Test 3: Verificar que SÍ detecta duplicado...")
    is_recent = dm.is_recent_same_run(
        property_name=property_name,
        start_date=start_date,
        end_date=end_date,
        nights=nights,
        guests=guests,
        platforms=platforms
    )
    
    if is_recent:
        print("   ✅ PASS: Duplicado detectado correctamente")
    else:
        print("   ❌ FAIL: No se detectó el duplicado")
        return False
    
    # Test 4: Configuración diferente NO debería detectar duplicado
    print(f"\n📋 Test 4: Configuración diferente (3 noches en vez de 2)...")
    is_recent = dm.is_recent_same_run(
        property_name=property_name,
        start_date=start_date,
        end_date=end_date,
        nights=3,  # Diferente!
        guests=guests,
        platforms=platforms
    )
    
    if not is_recent:
        print("   ✅ PASS: No se detectó duplicado (configuración diferente)")
    else:
        print("   ❌ FAIL: Se detectó duplicado erróneamente")
        return False
    
    # Test 5: Plataformas diferentes
    print(f"\n📋 Test 5: Solo Airbnb (plataformas diferentes)...")
    is_recent = dm.is_recent_same_run(
        property_name=property_name,
        start_date=start_date,
        end_date=end_date,
        nights=nights,
        guests=guests,
        platforms=['airbnb']  # Solo una plataforma
    )
    
    if not is_recent:
        print("   ✅ PASS: No se detectó duplicado (plataformas diferentes)")
    else:
        print("   ❌ FAIL: Se detectó duplicado erróneamente")
        return False
    
    # Test 6: Propiedad diferente
    print(f"\n📋 Test 6: Propiedad diferente...")
    is_recent = dm.is_recent_same_run(
        property_name="Otra Propiedad",
        start_date=start_date,
        end_date=end_date,
        nights=nights,
        guests=guests,
        platforms=platforms
    )
    
    if not is_recent:
        print("   ✅ PASS: No se detectó duplicado (propiedad diferente)")
    else:
        print("   ❌ FAIL: Se detectó duplicado erróneamente")
        return False
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
    print("=" * 60)
    
    # Mostrar el archivo de runs
    print(f"\n📄 Archivo de log: {dm.runs_path}")
    
    return True


if __name__ == '__main__':
    success = test_anti_duplicate()
    sys.exit(0 if success else 1)
