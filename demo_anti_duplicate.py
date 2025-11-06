"""
Demo visual del sistema anti-duplicado de 48 horas
Ejecutar con: python demo_anti_duplicate.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.data_manager import DataManager

def print_header(text):
    """Imprime un header estilizado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_config(name, start, end, nights, guests, platforms):
    """Imprime una configuración de scraping"""
    print(f"\n  📋 Configuración:")
    print(f"     • Propiedad: {name}")
    print(f"     • Fechas: {start} → {end}")
    print(f"     • Noches: {nights} | Huéspedes: {guests}")
    print(f"     • Plataformas: {', '.join(platforms)}")

def demo():
    """Demuestra el funcionamiento del sistema anti-duplicado"""
    
    dm = DataManager()
    
    print_header("🔒 DEMO: Sistema Anti-Duplicado de Scraping (48h)")
    
    # Configuración base
    property_name = "Aizeder Eco Container House"
    start_date = datetime.now().date()
    end_date = (datetime.now() + timedelta(days=7)).date()
    nights = 2
    guests = 2
    platforms = ['airbnb', 'booking']
    
    # ===== ESCENARIO 1 =====
    print_header("📍 ESCENARIO 1: Primera Ejecución")
    print_config(property_name, start_date, end_date, nights, guests, platforms)
    
    is_recent = dm.is_recent_same_run(
        property_name, start_date, end_date, nights, guests, platforms
    )
    
    print(f"\n  🔍 Verificando si existe ejecución reciente...")
    print(f"     Resultado: {'❌ SÍ (bloqueado)' if is_recent else '✅ NO (puede proceder)'}")
    
    if not is_recent:
        print(f"\n  🚀 Ejecutando scraping...")
        record = dm.log_scrape_run(
            property_name, start_date, end_date, nights, guests, platforms
        )
        print(f"     ✅ Scraping completado y registrado")
        print(f"     📅 Timestamp: {record['ts']}")
    
    # ===== ESCENARIO 2 =====
    print_header("📍 ESCENARIO 2: Intento de Re-ejecución (DUPLICADO)")
    print_config(property_name, start_date, end_date, nights, guests, platforms)
    
    is_recent = dm.is_recent_same_run(
        property_name, start_date, end_date, nights, guests, platforms
    )
    
    print(f"\n  🔍 Verificando si existe ejecución reciente...")
    print(f"     Resultado: {'❌ SÍ (bloqueado)' if is_recent else '✅ NO (puede proceder)'}")
    
    if is_recent:
        print(f"\n  ⚠️  WARNING: Ejecución duplicada detectada!")
        print(f"     Ya existe un scraping idéntico en las últimas 48h.")
        print(f"     Para ejecutar de todas formas, marca 'Forzar ejecución'.")
    
    # ===== ESCENARIO 3 =====
    print_header("📍 ESCENARIO 3: Configuración Diferente (3 noches)")
    nights_diff = 3
    print_config(property_name, start_date, end_date, nights_diff, guests, platforms)
    
    is_recent = dm.is_recent_same_run(
        property_name, start_date, end_date, nights_diff, guests, platforms
    )
    
    print(f"\n  🔍 Verificando si existe ejecución reciente...")
    print(f"     Resultado: {'❌ SÍ (bloqueado)' if is_recent else '✅ NO (puede proceder)'}")
    
    if not is_recent:
        print(f"\n  ✅ Parámetros diferentes detectados (noches: 2 → 3)")
        print(f"     El scraping puede proceder normalmente.")
    
    # ===== ESCENARIO 4 =====
    print_header("📍 ESCENARIO 4: Solo Airbnb (plataformas diferentes)")
    platforms_diff = ['airbnb']
    print_config(property_name, start_date, end_date, nights, guests, platforms_diff)
    
    is_recent = dm.is_recent_same_run(
        property_name, start_date, end_date, nights, guests, platforms_diff
    )
    
    print(f"\n  🔍 Verificando si existe ejecución reciente...")
    print(f"     Resultado: {'❌ SÍ (bloqueado)' if is_recent else '✅ NO (puede proceder)'}")
    
    if not is_recent:
        print(f"\n  ✅ Plataformas diferentes detectadas")
        print(f"     Original: airbnb, booking → Actual: airbnb")
        print(f"     El scraping puede proceder normalmente.")
    
    # ===== ESCENARIO 5 =====
    print_header("📍 ESCENARIO 5: Propiedad Diferente")
    property_diff = "Casa del Bosque"
    print_config(property_diff, start_date, end_date, nights, guests, platforms)
    
    is_recent = dm.is_recent_same_run(
        property_diff, start_date, end_date, nights, guests, platforms
    )
    
    print(f"\n  🔍 Verificando si existe ejecución reciente...")
    print(f"     Resultado: {'❌ SÍ (bloqueado)' if is_recent else '✅ NO (puede proceder)'}")
    
    if not is_recent:
        print(f"\n  ✅ Propiedad diferente detectada")
        print(f"     Original: {property_name}")
        print(f"     Actual: {property_diff}")
        print(f"     El scraping puede proceder normalmente.")
    
    # ===== RESUMEN =====
    print_header("📊 RESUMEN DE FUNCIONAMIENTO")
    
    print(f"\n  ✅ El sistema BLOQUEA cuando:")
    print(f"     • Propiedad + Fechas + Noches + Huéspedes + Plataformas son IDÉNTICOS")
    print(f"     • Y la ejecución anterior fue hace MENOS de 48 horas")
    
    print(f"\n  ✅ El sistema PERMITE cuando:")
    print(f"     • CUALQUIER parámetro es diferente")
    print(f"     • O han pasado MÁS de 48 horas desde la última ejecución")
    print(f"     • O el usuario marca 'Forzar ejecución' (override)")
    
    print(f"\n  📄 Log de ejecuciones guardado en:")
    print(f"     {dm.runs_path}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    demo()
