"""
Script de diagnóstico para probar el scraping y detectar problemas
"""
import sys
from datetime import datetime, timedelta
from database.db_manager import get_db
from scrapers.orchestrator import ejecutar_scraping
from playwright.sync_api import sync_playwright
from scrapers.utils.stealth import configurar_navegador_stealth
from scrapers.robots.booking_robot import BookingRobot
from scrapers.robots.airbnb_robot import AirbnbRobot

def probar_url_manualmente(plataforma: str, url: str, fecha_checkin: datetime):
    """Prueba una URL manualmente y muestra detalles del proceso"""
    print(f"\n{'='*80}")
    print(f"PRUEBA MANUAL DE SCRAPING")
    print(f"Plataforma: {plataforma}")
    print(f"URL: {url}")
    print(f"Fecha Check-in: {fecha_checkin.date()}")
    print(f"{'='*80}\n")
    
    # Crear navegador
    print("Iniciando navegador con modo stealth...")
    browser, context = configurar_navegador_stealth()
    
    try:
        # Crear el robot apropiado
        if plataforma == 'Booking':
            robot = BookingRobot()
        elif plataforma == 'Airbnb':
            robot = AirbnbRobot()
        else:
            print(f"ERROR: Plataforma '{plataforma}' no soportada")
            return
        
        print(f"Robot {plataforma} creado exitosamente")
        print(f"Selectores cargados: {list(robot.selectores.keys())}")
        
        # Probar con 3 noches
        print(f"\n--- INTENTANDO CON 3 NOCHES ---")
        url_3_noches = robot.construir_url(url, fecha_checkin, 3)
        print(f"URL generada: {url_3_noches[:100]}...")
        
        # Abrir página
        page = context.new_page()
        print("Navegando a la página...")
        page.goto(url_3_noches, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
        
        # Guardar screenshot
        screenshot_path = f"/workspaces/price-monitor/debug_{plataforma}_{fecha_checkin.date()}.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot guardado en: {screenshot_path}")
        
        # Verificar bloqueo
        if robot.detectar_bloqueo(page):
            print("⚠️  BLOQUEO/CAPTCHA DETECTADO")
        else:
            print("✓ No se detectó bloqueo")
        
        # Buscar selectores de precio
        print(f"\nBuscando selectores de precio:")
        for i, selector in enumerate(robot.selectores.get('precio', []), 1):
            count = page.locator(selector).count()
            print(f"  {i}. {selector}: {count} elementos encontrados")
            if count > 0:
                try:
                    texto = page.locator(selector).first.inner_text()
                    print(f"     Texto: '{texto}'")
                except:
                    print(f"     (No se pudo extraer texto)")
        
        # Buscar selectores de no disponible
        print(f"\nBuscando selectores de 'no disponible':")
        for i, selector in enumerate(robot.selectores.get('no_disponible', []), 1):
            count = page.locator(selector).count()
            print(f"  {i}. {selector}: {count} elementos encontrados")
        
        # Obtener HTML parcial para análisis
        print(f"\n--- HTML PARCIAL (primeros 1000 chars del body) ---")
        try:
            body_html = page.locator('body').inner_html()
            print(body_html[:1000])
        except:
            print("No se pudo extraer HTML del body")
        
        page.close()
        
        # Ahora probar con el método buscar del robot
        print(f"\n{'='*80}")
        print(f"EJECUTANDO MÉTODO buscar() DEL ROBOT")
        print(f"{'='*80}\n")
        
        resultado = robot.buscar(browser, url, fecha_checkin)
        
        print(f"\nRESULTADO:")
        print(f"  Precio: ${resultado['precio']}")
        print(f"  Noches: {resultado['noches']}")
        print(f"  Detalles: {resultado['detalles']}")
        print(f"  Error: {resultado['error']}")
        
    finally:
        context.close()
        browser.close()
        print("\nNavegador cerrado")

def analizar_datos_bd():
    """Analiza los datos en la base de datos para detectar patrones de error"""
    print(f"\n{'='*80}")
    print(f"ANÁLISIS DE BASE DE DATOS")
    print(f"{'='*80}\n")
    
    db = get_db()
    
    # Obtener todas las URLs
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Resumen por plataforma
        cursor.execute("""
            SELECT 
                plataforma,
                COUNT(*) as total_urls,
                SUM(CASE WHEN esta_activa THEN 1 ELSE 0 END) as urls_activas
            FROM Plataformas_URL
            GROUP BY plataforma
        """)
        
        print("URLs por Plataforma:")
        for row in cursor.fetchall():
            print(f"  {row['plataforma']}: {row['urls_activas']}/{row['total_urls']} activas")
        
        # Análisis de errores
        cursor.execute("""
            SELECT 
                p.plataforma,
                COUNT(*) as total_intentos,
                SUM(CASE WHEN pr.precio_base > 0 THEN 1 ELSE 0 END) as exitos,
                SUM(CASE WHEN pr.precio_base = 0 THEN 1 ELSE 0 END) as fallos,
                COUNT(DISTINCT pr.error_log) as tipos_error
            FROM Precios pr
            JOIN Plataformas_URL p ON pr.id_plataforma_url = p.id_plataforma_url
            GROUP BY p.plataforma
        """)
        
        print("\nEstadísticas de Scraping:")
        for row in cursor.fetchall():
            tasa_exito = (row['exitos'] / row['total_intentos'] * 100) if row['total_intentos'] > 0 else 0
            print(f"  {row['plataforma']}:")
            print(f"    Total intentos: {row['total_intentos']}")
            print(f"    Éxitos: {row['exitos']} ({tasa_exito:.1f}%)")
            print(f"    Fallos: {row['fallos']}")
            print(f"    Tipos de error: {row['tipos_error']}")
        
        # Errores más comunes
        cursor.execute("""
            SELECT 
                error_log,
                COUNT(*) as frecuencia
            FROM Precios
            WHERE error_log IS NOT NULL
            GROUP BY error_log
            ORDER BY frecuencia DESC
            LIMIT 5
        """)
        
        print("\nErrores Más Comunes:")
        for row in cursor.fetchall():
            print(f"  [{row['frecuencia']}x] {row['error_log']}")

def main():
    print("SCRIPT DE DIAGNÓSTICO - PRICE MONITOR")
    print("="*80)
    
    # Primero analizar BD
    analizar_datos_bd()
    
    # Obtener URLs de prueba
    db = get_db()
    urls_activas = db.get_urls_activas_by_establecimiento(5)  # ID del establecimiento
    
    if not urls_activas:
        print("\n❌ No hay URLs activas para probar")
        return
    
    print(f"\n\nURLs disponibles para prueba:")
    for i, url_info in enumerate(urls_activas, 1):
        print(f"  {i}. {url_info['plataforma']}: {url_info['url'][:60]}...")
    
    # Probar una URL manualmente
    opcion = input("\n¿Qué URL quieres probar? (número o 'n' para ninguna): ")
    
    if opcion.lower() != 'n':
        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(urls_activas):
                url_info = urls_activas[idx]
                fecha_prueba = datetime.now() + timedelta(days=7)  # 1 semana desde hoy
                
                probar_url_manualmente(
                    url_info['plataforma'],
                    url_info['url'],
                    fecha_prueba
                )
            else:
                print("Opción inválida")
        except ValueError:
            print("Entrada inválida")

if __name__ == "__main__":
    main()
