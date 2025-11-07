#!/usr/bin/env python3
"""
Test de la nueva lógica de UPSERT INTELIGENTE.
Valida que NO se sobrescriban precios válidos con precios=0.
"""

import sys
from pathlib import Path
from datetime import datetime
import sqlite3

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import get_db


def test_upsert_inteligente():
    """
    Prueba la lógica de UPSERT inteligente con el escenario real.
    """
    print("="*70)
    print("TEST: UPSERT INTELIGENTE - Preservación de Precios Válidos")
    print("="*70)
    print()
    
    db = get_db()
    
    # Limpiar datos de prueba anteriores
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Buscar una URL de Airbnb activa
        cursor.execute("""
            SELECT id_plataforma_url 
            FROM Plataformas_URL 
            WHERE plataforma = 'Airbnb' AND esta_activa = 1
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if not row:
            print("❌ Error: No hay URLs de Airbnb activas en la BD")
            return
        
        id_url = row[0]
        print(f"📌 Usando id_plataforma_url: {id_url}")
        print()
        
        # Limpiar datos de prueba previos
        cursor.execute("""
            DELETE FROM Precios 
            WHERE id_plataforma_url = ? 
            AND fecha_noche IN ('2025-11-07', '2025-11-08')
        """, (id_url,))
        conn.commit()
    
    print("ESCENARIO:")
    print("1. Búsqueda '7nov-2n' encuentra precio → Guarda 7 y 8 nov con $150")
    print("2. Búsqueda '8nov-2n' NO encuentra → Intenta guardar 8 nov con $0")
    print("3. ¿El precio del 8 nov se preserva?")
    print()
    
    # Paso 1: Búsqueda exitosa (7 nov, 2 noches)
    print("PASO 1: Búsqueda '7nov-2n' EXITOSA")
    print("-" * 40)
    
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=datetime(2025, 11, 7),
        precio_base=150.0,
        noches_encontradas=2
    )
    print("✓ Guardado: 7 nov → $150 (2 noches)")
    
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=datetime(2025, 11, 8),
        precio_base=150.0,
        noches_encontradas=2
    )
    print("✓ Guardado: 8 nov → $150 (2 noches)")
    print()
    
    # Verificar datos guardados
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fecha_noche, precio_base, noches_encontradas
            FROM Precios
            WHERE id_plataforma_url = ?
            AND fecha_noche IN ('2025-11-07', '2025-11-08')
            ORDER BY fecha_noche
        """, (id_url,))
        
        print("Estado actual de la BD:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: ${row[1]:.2f} ({row[2]} noches)")
    print()
    
    # Paso 2: Búsqueda fallida (8 nov, 2 noches) - Intenta sobrescribir
    print("PASO 2: Búsqueda '8nov-2n' FALLIDA (intenta sobrescribir)")
    print("-" * 40)
    
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=datetime(2025, 11, 8),
        precio_base=0.0,  # ← Precio = 0 (no disponible)
        noches_encontradas=0
    )
    print("⚠️  Intentó guardar: 8 nov → $0 (0 noches)")
    print()
    
    # Verificar si se preservó el precio
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fecha_noche, precio_base, noches_encontradas
            FROM Precios
            WHERE id_plataforma_url = ?
            AND fecha_noche IN ('2025-11-07', '2025-11-08')
            ORDER BY fecha_noche
        """, (id_url,))
        
        print("Estado DESPUÉS del intento de sobrescritura:")
        resultados = cursor.fetchall()
        for row in resultados:
            print(f"  {row[0]}: ${row[1]:.2f} ({row[2]} noches)")
        
        # Validar que el precio se preservó
        precio_8nov = next((r[1] for r in resultados if r[0] == '2025-11-08'), None)
        
        print()
        print("="*70)
        print("RESULTADO:")
        print("="*70)
        
        if precio_8nov == 150.0:
            print("✅ SUCCESS: El precio del 8 nov se PRESERVÓ correctamente")
            print("   Valor esperado: $150.00")
            print(f"   Valor actual:   ${precio_8nov:.2f}")
            print()
            print("👍 La lógica de UPSERT INTELIGENTE funciona correctamente")
            print("   NO sobrescribe precios válidos con precios=0")
        else:
            print(f"❌ FAILED: El precio se sobrescribió incorrectamente")
            print("   Valor esperado: $150.00")
            print(f"   Valor actual:   ${precio_8nov:.2f}")
            print()
            print("⚠️  La lógica necesita ajustes")
        
        print("="*70)
    
    # Test adicional: Actualización de precio válido por otro válido
    print()
    print("TEST ADICIONAL: Actualización precio válido → precio válido")
    print("-" * 40)
    
    db.upsert_precio(
        id_plataforma_url=id_url,
        fecha_noche=datetime(2025, 11, 7),
        precio_base=160.0,  # Nuevo precio válido
        noches_encontradas=2
    )
    print("✓ Actualizado: 7 nov → $160 (nuevo precio válido)")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT precio_base
            FROM Precios
            WHERE id_plataforma_url = ?
            AND fecha_noche = '2025-11-07'
        """, (id_url,))
        
        nuevo_precio = cursor.fetchone()[0]
        
        if nuevo_precio == 160.0:
            print(f"✅ SUCCESS: Precio actualizado correctamente a ${nuevo_precio:.2f}")
        else:
            print(f"❌ FAILED: Precio no se actualizó. Valor: ${nuevo_precio:.2f}")
    
    print()


if __name__ == '__main__':
    test_upsert_inteligente()
