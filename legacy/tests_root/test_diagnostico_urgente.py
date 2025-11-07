"""
DIAGNÓSTICO URGENTE: Test directo para identificar por qué no se guardan datos
Verifica cada paso del proceso de scraping
"""
import sqlite3
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_estado_sistema():
    """Verifica el estado completo del sistema"""
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO URGENTE DEL SISTEMA DE SCRAPING")
    print("="*80)
    
    # 1. VERIFICAR BASE DE DATOS
    print("\n1. VERIFICANDO BASE DE DATOS...")
    db_path = "./database/price_monitor.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Contar establecimientos
    cursor.execute("SELECT COUNT(*) FROM Establecimientos")
    total_est = cursor.fetchone()[0]
    print(f"   ✓ Establecimientos en DB: {total_est}")
    
    # Contar URLs activas
    cursor.execute("SELECT COUNT(*) FROM Plataformas_URL WHERE esta_activa = TRUE")
    total_urls = cursor.fetchone()[0]
    print(f"   ✓ URLs activas: {total_urls}")
    
    # Contar precios
    cursor.execute("SELECT COUNT(*) FROM Precios")
    total_precios = cursor.fetchone()[0]
    print(f"   ✗ Precios guardados: {total_precios} (PROBLEMA: Debería tener datos)")
    
    # Verificar establecimientos con detalles
    print("\n2. ESTABLECIMIENTOS REGISTRADOS:")
    cursor.execute("""
        SELECT e.id_establecimiento, e.nombre_personalizado,
               COUNT(p.id_plataforma_url) as urls_count
        FROM Establecimientos e
        LEFT JOIN Plataformas_URL p ON e.id_establecimiento = p.id_establecimiento
        GROUP BY e.id_establecimiento
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   - ID {row[0]}: {row[1]} ({row[2]} URLs)")
    
    # Obtener una URL de Airbnb para probar
    print("\n3. OBTENIENDO URL DE AIRBNB PARA PRUEBA...")
    cursor.execute("""
        SELECT id_plataforma_url, id_establecimiento, url 
        FROM Plataformas_URL 
        WHERE plataforma = 'Airbnb' AND esta_activa = TRUE 
        LIMIT 1
    """)
    url_data = cursor.fetchone()
    
    if not url_data:
        print("   ✗ NO HAY URLs DE AIRBNB ACTIVAS")
        conn.close()
        return None
    
    id_plataforma_url, id_establecimiento, url = url_data
    print(f"   ✓ URL encontrada: {url[:80]}...")
    print(f"   ✓ ID Plataforma URL: {id_plataforma_url}")
    print(f"   ✓ ID Establecimiento: {id_establecimiento}")
    
    conn.close()
    
    # 4. VERIFICAR LÓGICA DE 48H
    print("\n4. VERIFICANDO LÓGICA DE 48 HORAS...")
    fecha_inicio = datetime(2025, 11, 7)
    fecha_fin = datetime(2025, 11, 13)
    
    from database.db_manager import get_db
    db = get_db()
    fechas_a_scrapear = db.get_fechas_a_scrapear(id_plataforma_url, fecha_inicio, fecha_fin)
    print(f"   ✓ Fechas que necesitan scraping: {len(fechas_a_scrapear)}")
    for fecha in fechas_a_scrapear[:3]:
        print(f"     - {fecha.date()}")
    if len(fechas_a_scrapear) > 3:
        print(f"     ... y {len(fechas_a_scrapear) - 3} más")
    
    # 5. TEST DE INSERCIÓN DIRECTA
    print("\n5. PROBANDO INSERCIÓN DIRECTA EN BASE DE DATOS...")
    try:
        test_fecha = datetime(2025, 11, 7)
        db.upsert_precio(
            id_plataforma_url=id_plataforma_url,
            fecha_noche=test_fecha,
            precio_base=100.50,
            noches_encontradas=1,
            incluye_limpieza='No Informa',
            incluye_impuestos='No Informa',
            ofrece_desayuno='No Informa',
            error_log='TEST DE DIAGNÓSTICO'
        )
        print("   ✓ Inserción de prueba EXITOSA")
        
        # Verificar que se guardó
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT precio_base, fecha_scrape FROM Precios 
            WHERE id_plataforma_url = ? AND fecha_noche = ?
        """, (id_plataforma_url, test_fecha.date()))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"   ✓ Dato verificado en DB: Precio=${resultado[0]}, Scrape={resultado[1]}")
            
            # Limpiar el dato de prueba
            cursor.execute("""
                DELETE FROM Precios 
                WHERE id_plataforma_url = ? AND fecha_noche = ? AND error_log = 'TEST DE DIAGNÓSTICO'
            """, (id_plataforma_url, test_fecha.date()))
            conn.commit()
            print("   ✓ Dato de prueba eliminado")
        conn.close()
    except Exception as e:
        print(f"   ✗ ERROR en inserción: {e}")
        return None
    
    # 6. ANÁLISIS DE LOGS
    print("\n6. ANALIZANDO ÚLTIMOS LOGS DE SCRAPING...")
    try:
        with open('./logs/scraping.log', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            # Buscar las últimas líneas relevantes
            lineas_relevantes = []
            for linea in reversed(lineas[-200:]):
                if any(keyword in linea for keyword in ['Precio encontrado', 'No disponible', 'Guardando', 'upsert']):
                    lineas_relevantes.append(linea.strip())
                if len(lineas_relevantes) >= 10:
                    break
            
            if lineas_relevantes:
                print("   Últimas operaciones relevantes:")
                for linea in reversed(lineas_relevantes):
                    print(f"   {linea[:120]}")
            else:
                print("   ⚠ No se encontraron operaciones de guardado en los logs recientes")
    except Exception as e:
        print(f"   ⚠ Error leyendo logs: {e}")
    
    print("\n" + "="*80)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("="*80)
    print(f"✓ Base de datos: OK ({total_est} establecimientos, {total_urls} URLs)")
    print(f"✗ Precios guardados: {total_precios} (PROBLEMA CRÍTICO)")
    print(f"✓ Lógica de inserción: FUNCIONA")
    print(f"✓ Fechas a scrapear: {len(fechas_a_scrapear)} detectadas")
    print("")
    print("CONCLUSIÓN:")
    if total_precios == 0 and len(fechas_a_scrapear) > 0:
        print("❌ El scraping NO ESTÁ GUARDANDO los datos extraídos")
        print("   Posibles causas:")
        print("   1. El robot no encuentra precios (selectores desactualizados)")
        print("   2. El orchestrator no llama a _guardar_resultado()")
        print("   3. Hay un error silencioso en el proceso de guardado")
    print("="*80)
    
    return {
        'id_plataforma_url': id_plataforma_url,
        'url': url,
        'fechas_a_scrapear': fechas_a_scrapear[:7]  # Solo primeras 7 fechas
    }

if __name__ == "__main__":
    info = verificar_estado_sistema()
    
    if info and info['fechas_a_scrapear']:
        print("\n🔍 RECOMENDACIÓN INMEDIATA:")
        print("1. Ejecutar scraping para una fecha específica con debug activado")
        print("2. Verificar si _guardar_resultado() se está llamando en orchestrator.py")
        print("3. Revisar los selectores de Airbnb en selectors.json")
        print("\nPara test rápido, ejecuta:")
        print(f"   python test_scraping_quick.py --url-id {info['id_plataforma_url']} --fecha 2025-11-07")
