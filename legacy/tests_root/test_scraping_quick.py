"""
Script de prueba rápida del scraping mejorado
Ejecuta una prueba simple con una URL para verificar las mejoras
"""
import sys
from datetime import datetime, timedelta
from database.db_manager import get_db
from scrapers.utils.stealth import configurar_navegador_stealth
from scrapers.robots.booking_robot import BookingRobot
from scrapers.robots.airbnb_robot import AirbnbRobot
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_url(plataforma: str, url: str):
    """Prueba una URL específica"""
    logger.info(f"\n{'='*80}")
    logger.info(f"PRUEBA DE SCRAPING - {plataforma}")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*80}\n")
    
    # Fecha de prueba: 1 semana desde hoy
    fecha_prueba = datetime.now() + timedelta(days=7)
    logger.info(f"Fecha de check-in: {fecha_prueba.date()}")
    
    # Iniciar navegador
    logger.info("Iniciando navegador con modo stealth...")
    browser, context = configurar_navegador_stealth()
    
    try:
        # Crear robot
        if plataforma == 'Booking':
            robot = BookingRobot()
        elif plataforma == 'Airbnb':
            robot = AirbnbRobot()
        else:
            logger.error(f"Plataforma no soportada: {plataforma}")
            return
        
        logger.info(f"Robot {plataforma} creado")
        
        # Ejecutar búsqueda
        logger.info("Ejecutando búsqueda con lógica 3->2->1 noches...")
        resultado = robot.buscar(browser, url, fecha_prueba)
        
        # Mostrar resultados
        logger.info(f"\n{'='*80}")
        logger.info("RESULTADO:")
        logger.info(f"  Precio: ${resultado['precio']}")
        logger.info(f"  Noches encontradas: {resultado['noches']}")
        logger.info(f"  Detalles: {resultado['detalles']}")
        logger.info(f"  Error: {resultado['error']}")
        logger.info(f"{'='*80}\n")
        
        if resultado['precio'] > 0:
            logger.info("✅ ¡ÉXITO! Se encontró un precio")
        else:
            logger.warning("❌ No se encontró precio disponible")
            
    except Exception as e:
        logger.error(f"Error durante la prueba: {e}", exc_info=True)
    finally:
        context.close()
        browser.close()
        logger.info("Navegador cerrado")

def main():
    """Función principal"""
    print("\n🧪 PRUEBA RÁPIDA DE SCRAPING MEJORADO\n")
    
    # Obtener URLs de la base de datos
    db = get_db()
    urls_activas = db.get_urls_activas_by_establecimiento(5)  # ID de Viento de Glaciares
    
    if not urls_activas:
        print("❌ No hay URLs activas en la base de datos")
        return
    
    print("URLs disponibles:")
    for i, url_info in enumerate(urls_activas, 1):
        print(f"  {i}. {url_info['plataforma']}: {url_info['url'][:60]}...")
    
    # Preguntar qué URL probar
    try:
        opcion = input("\n¿Qué URL quieres probar? (1, 2, etc.): ")
        idx = int(opcion) - 1
        
        if 0 <= idx < len(urls_activas):
            url_info = urls_activas[idx]
            test_url(url_info['plataforma'], url_info['url'])
        else:
            print("❌ Opción inválida")
    except (ValueError, KeyboardInterrupt):
        print("\n❌ Cancelado")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
