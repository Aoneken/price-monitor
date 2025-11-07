"""
TEST RÁPIDO - Robot Airbnb V2
Prueba directa con una URL real para validar la solución
"""
from datetime import datetime
import logging
from scrapers.utils.stealth import configurar_navegador_stealth
from scrapers.robots.airbnb_robot_v2 import AirbnbRobotV2
from database.db_manager import get_db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_robot_v2():
    print("\n" + "="*80)
    print("TEST RÁPIDO: AIRBNB ROBOT V2")
    print("="*80)
    
    # 1. Obtener URL real de la base de datos
    db = get_db()
    import sqlite3
    conn = sqlite3.connect("./database/price_monitor.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_plataforma_url, id_establecimiento, url 
        FROM Plataformas_URL 
        WHERE plataforma = 'Airbnb' AND esta_activa = TRUE 
        LIMIT 1
    """)
    url_data = cursor.fetchone()
    conn.close()
    
    if not url_data:
        print("❌ No hay URLs de Airbnb en la base de datos")
        return
    
    id_plataforma_url, id_establecimiento, url_base = url_data
    print(f"\n✓ URL a probar: {url_base[:80]}...")
    print(f"✓ ID Plataforma URL: {id_plataforma_url}")
    
    # 2. Configurar navegador
    print("\n📡 Inicializando navegador con modo stealth...")
    browser, context = configurar_navegador_stealth()
    
    # 3. Crear robot V2
    robot = AirbnbRobotV2()
    
    # 4. Probar con una fecha específica
    fecha_checkin = datetime(2025, 11, 8)  # 8 de noviembre
    print(f"\n🔍 Buscando precio para: {fecha_checkin.date()}")
    print("="*80)
    
    try:
        resultado = robot.buscar(browser, url_base, fecha_checkin)
        
        print("\n" + "="*80)
        print("RESULTADO DEL SCRAPING:")
        print("="*80)
        print(f"Precio por noche: ${resultado['precio']:.2f}")
        print(f"Noches encontradas: {resultado['noches']}")
        print(f"Detalles: {resultado['detalles']}")
        print(f"Error: {resultado['error']}")
        
        # 5. Guardar en base de datos si encontró precio
        if resultado['precio'] > 0:
            print("\n✅ ¡PRECIO ENCONTRADO! Guardando en base de datos...")
            
            # Determinar fechas a guardar basado en noches encontradas
            from datetime import timedelta
            noches = resultado['noches']
            fechas_a_guardar = [fecha_checkin + timedelta(days=i) for i in range(noches)]
            
            for fecha in fechas_a_guardar:
                db.upsert_precio(
                    id_plataforma_url=id_plataforma_url,
                    fecha_noche=fecha,
                    precio_base=resultado['precio'],
                    noches_encontradas=noches,
                    incluye_limpieza='No Informa',
                    incluye_impuestos='No Informa',
                    ofrece_desayuno='No Informa',
                    error_log=None
                )
                print(f"  ✓ Guardado: {fecha.date()} - ${resultado['precio']:.2f}")
            
            # Verificar que se guardó
            conn = sqlite3.connect("./database/price_monitor.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Precios WHERE id_plataforma_url = ?", (id_plataforma_url,))
            total = cursor.fetchone()[0]
            conn.close()
            print(f"\n✅ Total de precios en BD para esta URL: {total}")
        else:
            print("\n⚠️ No se encontró precio (puede estar no disponible)")
            if resultado['error']:
                print(f"   Razón: {resultado['error']}")
        
    except Exception as e:
        print(f"\n❌ ERROR durante el scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 6. Cerrar navegador
        print("\n🔒 Cerrando navegador...")
        context.close()
        browser.close()
    
    print("\n" + "="*80)
    print("TEST COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    test_robot_v2()
