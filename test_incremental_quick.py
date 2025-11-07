"""
Test rápido del algoritmo incremental.

Este script prueba el scheduler incremental con:
- 1 URL de prueba (Viento de Glaciares - Booking)
- Rango de 7 días
- Sin caché
- Modo visible (no headless) para debugging
"""
from datetime import date, timedelta
import sys
from pathlib import Path

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from scripts.scheduler_incremental_v3 import IncrementalScraperScheduler


def test_incremental():
    """Test básico del algoritmo incremental."""
    print("\n" + "="*70)
    print("TEST: Algoritmo de Búsqueda Incremental")
    print("="*70)
    
    # Crear scheduler (sin caché, visible)
    scheduler = IncrementalScraperScheduler(
        cache_hours=0,  # Desactivar caché para testing
        headless=False  # Modo visible para debugging
    )
    
    # Rango de prueba: 7 días adelante
    start_date = date.today() + timedelta(days=7)
    end_date = start_date + timedelta(days=6)  # 7 días totales
    
    print(f"\nRango de prueba: {start_date} → {end_date}")
    print(f"Total: {(end_date - start_date).days + 1} días\n")
    
    # Ejecutar solo para Booking
    stats = scheduler.scrape_all_urls_date_range(
        start_date=start_date,
        end_date=end_date,
        platform_filter='Booking',
        establishment_filter=None  # Todas las propiedades de Booking
    )
    
    # Análisis
    print("\n" + "="*70)
    print("ANÁLISIS DE RESULTADOS")
    print("="*70)
    
    total_fechas = sum([
        stats['success_3'] * 3,
        stats['success_2'] * 2,
        stats['success_1'],
        stats['occupied']
    ])
    
    print(f"URLs procesadas:       {stats['total_urls']}")
    print(f"Fechas resueltas:      {total_fechas}")
    print(f"Requests realizados:   {stats['requests_made']}")
    print(f"\nDistribución de éxitos:")
    print(f"  3 noches: {stats['success_3']} búsquedas → {stats['success_3'] * 3} fechas")
    print(f"  2 noches: {stats['success_2']} búsquedas → {stats['success_2'] * 2} fechas")
    print(f"  1 noche:  {stats['success_1']} búsquedas → {stats['success_1']} fechas")
    print(f"  Ocupadas: {stats['occupied']} fechas")
    print(f"  En caché: {stats['cached']} fechas (omitidas)")
    
    # Calcular ahorro
    sin_algoritmo = stats['total_urls'] * 7  # 1 request por día por URL
    con_algoritmo = stats['requests_made']
    ahorro = ((sin_algoritmo - con_algoritmo) / sin_algoritmo * 100) if sin_algoritmo > 0 else 0
    
    print(f"\nEficiencia:")
    print(f"  Sin algoritmo: ~{sin_algoritmo} requests (1 por fecha)")
    print(f"  Con algoritmo: {con_algoritmo} requests")
    print(f"  Ahorro:        {ahorro:.1f}%")
    print(f"  Eficiencia:    {stats['efficiency']:.1f}% (fechas por request)")
    
    print("="*70)
    
    # Verificar lógica
    assert total_fechas + stats['cached'] == stats['total_dates'], \
        "ERROR: Fechas resueltas no coinciden con total"
    
    print("\n✅ Test completado con éxito!")


if __name__ == '__main__':
    test_incremental()
