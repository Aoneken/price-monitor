#!/usr/bin/env python3
"""
Script para procesar archivos HTML guardados en debug/
y extraer precios usando la lógica mejorada sin hacer scraping.

Permite:
1. Validar la extracción de precios
2. Refinar selectores y métodos de extracción
3. Actualizar la base de datos con datos reales
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
from database.db_manager import get_db


def parsear_nombre_archivo(filename: str) -> Optional[Tuple[str, datetime, int]]:
    """
    Parsea el nombre del archivo para extraer información.
    Formato: airbnb_YYYYMMDD_Nn_HHMMSS.html
    
    Returns:
        (plataforma, fecha, noches) o None si no puede parsear
    """
    pattern = r'(\w+)_(\d{8})_(\d+)n_\d+\.html'
    match = re.match(pattern, filename)
    
    if match:
        plataforma = match.group(1).capitalize()
        fecha_str = match.group(2)
        noches = int(match.group(3))
        
        # Convertir fecha
        fecha = datetime.strptime(fecha_str, '%Y%m%d')
        
        return (plataforma, fecha, noches)
    
    return None


def validar_precio(texto: str) -> bool:
    """Valida que el precio esté en un rango razonable (misma lógica que airbnb_robot.py)"""
    try:
        numeros = re.sub(r'[^\d]', '', texto)
        if not numeros:
            return False
        precio = float(numeros)
        return 10 <= precio <= 10000
    except:
        return False


def extraer_precio_de_html(html_content: str, mostrar_debug: bool = False) -> Optional[float]:
    """
    Extrae precio del contenido HTML usando Playwright para parsear.
    Usa la misma lógica que airbnb_robot.py mejorado.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Cargar el HTML
        page.set_content(html_content)
        
        # Selectores mejorados (mismos que en airbnb_robot.py)
        selectores_mejorados = [
            'div[data-section-id="BOOK_IT_SIDEBAR"] span[class*="_14y1gc"]',
            'span._tyxjp1',
            'span._1k4xcdh',
            'div._1jo4hgw',
            'span[class*="price"]',
            'div[class*="PriceLockup"]',
            'span[class*="_tyxjp1"]',
            'div[class*="_1y74zjx"]',
        ]
        
        # Intentar con selectores
        for selector in selectores_mejorados:
            try:
                elementos = page.query_selector_all(selector)
                for elemento in elementos:
                    texto = elemento.inner_text().strip()
                    if texto and '$' in texto and any(char.isdigit() for char in texto):
                        if validar_precio(texto):
                            # Extraer solo los números
                            numeros = re.sub(r'[^\d]', '', texto)
                            precio = float(numeros)
                            if mostrar_debug:
                                print(f"      ✓ Encontrado con selector: {selector[:50]}")
                                print(f"        Texto: '{texto}' -> Precio: ${precio:.2f}")
                            browser.close()
                            return precio
            except Exception as e:
                if mostrar_debug:
                    print(f"      ✗ Error con selector {selector[:30]}: {e}")
                continue
        
        # Buscar en texto completo como fallback
        try:
            page_text = page.inner_text('body')
            price_patterns = [
                r'\$\s*([0-9,]+)\s*USD',
                r'USD\s*\$?\s*([0-9,]+)',
                r'\$\s*([0-9,]+)\s+por\s+noche',
                r'\$\s*([0-9,]+)\s*noche',
                r'\$\s*([0-9,]+)\s*total',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    precio_texto = match.group(0)
                    if validar_precio(precio_texto):
                        numeros = re.sub(r'[^\d]', '', precio_texto)
                        precio = float(numeros)
                        if mostrar_debug:
                            print(f"      ✓ Encontrado con regex: {pattern}")
                            print(f"        Precio: ${precio:.2f}")
                        browser.close()
                        return precio
        except:
            pass
        
        browser.close()
        return None


def procesar_archivos_debug(
    debug_dir: Path,
    actualizar_bd: bool = False,
    mostrar_debug: bool = False
) -> List[Dict]:
    """
    Procesa todos los archivos HTML en el directorio debug.
    
    Args:
        debug_dir: Directorio con archivos HTML
        actualizar_bd: Si True, actualiza la base de datos
        mostrar_debug: Si True, muestra información detallada
    
    Returns:
        Lista de resultados procesados
    """
    archivos_html = sorted(debug_dir.glob('*.html'))
    resultados = []
    
    print(f"\n{'='*70}")
    print(f"PROCESANDO {len(archivos_html)} ARCHIVOS HTML DE DEBUG")
    print(f"{'='*70}\n")
    
    db = get_db() if actualizar_bd else None
    
    # Primero necesitamos obtener el ID de la URL de Airbnb
    id_plataforma_url = None
    if actualizar_bd:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            # Buscar la primera URL de Airbnb activa
            cursor.execute("""
                SELECT id_plataforma_url 
                FROM Plataformas_URL 
                WHERE plataforma = 'Airbnb' AND esta_activa = 1
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                id_plataforma_url = row[0]
                print(f"📌 Usando id_plataforma_url: {id_plataforma_url}\n")
            else:
                print("⚠️  No se encontró URL de Airbnb activa. No se actualizará la BD.\n")
                actualizar_bd = False
    
    for idx, html_file in enumerate(archivos_html, 1):
        # Parsear nombre del archivo
        info = parsear_nombre_archivo(html_file.name)
        if not info:
            print(f"[{idx}/{len(archivos_html)}] ⚠️  No se pudo parsear: {html_file.name}")
            continue
        
        plataforma, fecha_checkin, noches = info
        
        print(f"[{idx}/{len(archivos_html)}] 📄 {html_file.name}")
        print(f"    Fecha: {fecha_checkin.date()}, Noches: {noches}")
        
        # Leer HTML
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"    ✗ Error leyendo archivo: {e}\n")
            continue
        
        # Extraer precio
        precio = extraer_precio_de_html(html_content, mostrar_debug)
        
        if precio:
            precio_por_noche = precio / noches
            print(f"    ✅ Precio encontrado: ${precio:.2f} total (${precio_por_noche:.2f}/noche)")
            
            # Guardar en BD si está habilitado
            if actualizar_bd and id_plataforma_url:
                # Guardar para TODAS las noches del período
                fechas_guardar = [fecha_checkin + timedelta(days=i) for i in range(noches)]
                print(f"    💾 Guardando en BD para fechas: {[f.date() for f in fechas_guardar]}")
                
                for fecha_guardar in fechas_guardar:
                    try:
                        db.upsert_precio(
                            id_plataforma_url=id_plataforma_url,
                            fecha_noche=fecha_guardar,
                            precio_base=precio_por_noche,
                            noches_encontradas=noches,
                            incluye_limpieza='No Informa',
                            incluye_impuestos='No Informa',
                            ofrece_desayuno='No Informa',
                            error_log=None
                        )
                    except Exception as e:
                        print(f"    ✗ Error guardando {fecha_guardar.date()}: {e}")
            
            resultado = {
                'archivo': html_file.name,
                'fecha': fecha_checkin,
                'noches': noches,
                'precio_total': precio,
                'precio_por_noche': precio_por_noche,
                'exito': True
            }
        else:
            print(f"    ❌ No se encontró precio (puede estar no disponible)")
            resultado = {
                'archivo': html_file.name,
                'fecha': fecha_checkin,
                'noches': noches,
                'precio_total': 0,
                'precio_por_noche': 0,
                'exito': False
            }
        
        resultados.append(resultado)
        print()
    
    return resultados


def mostrar_resumen(resultados: List[Dict]):
    """Muestra un resumen de los resultados"""
    print(f"\n{'='*70}")
    print("RESUMEN DE PROCESAMIENTO")
    print(f"{'='*70}\n")
    
    exitosos = [r for r in resultados if r['exito']]
    fallidos = [r for r in resultados if not r['exito']]
    
    print(f"Total archivos procesados: {len(resultados)}")
    print(f"✅ Precios encontrados: {len(exitosos)}")
    print(f"❌ Sin precio/No disponible: {len(fallidos)}")
    print()
    
    if exitosos:
        print("Precios encontrados por fecha y noches:")
        print("-" * 50)
        
        # Agrupar por fecha
        por_fecha = {}
        for r in exitosos:
            fecha_str = r['fecha'].strftime('%Y-%m-%d')
            if fecha_str not in por_fecha:
                por_fecha[fecha_str] = []
            por_fecha[fecha_str].append(r)
        
        for fecha in sorted(por_fecha.keys()):
            print(f"\n📅 {fecha}:")
            for r in por_fecha[fecha]:
                print(f"   {r['noches']}n: ${r['precio_total']:>8.2f} total (${r['precio_por_noche']:.2f}/noche)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Procesar archivos HTML de debug para extraer precios'
    )
    parser.add_argument(
        '--actualizar-bd',
        action='store_true',
        help='Actualizar la base de datos con los precios extraídos'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Mostrar información detallada de extracción'
    )
    
    args = parser.parse_args()
    
    # Directorio debug
    debug_dir = Path(__file__).parent / 'debug'
    
    if not debug_dir.exists():
        print(f"❌ Error: No existe el directorio {debug_dir}")
        sys.exit(1)
    
    # Procesar archivos
    resultados = procesar_archivos_debug(
        debug_dir,
        actualizar_bd=args.actualizar_bd,
        mostrar_debug=args.debug
    )
    
    # Mostrar resumen
    mostrar_resumen(resultados)
    
    if args.actualizar_bd:
        print("\n" + "="*70)
        print("✅ Base de datos actualizada con los precios encontrados")
        print("="*70)
