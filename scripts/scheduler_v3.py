"""
Scheduler automático de scraping V3.

Lee URLs de la BD, ejecuta scraping con orchestrator V3,
guarda resultados en BD.
"""
import sys
from datetime import date, timedelta
from pathlib import Path
import logging
from typing import List, Dict

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator_v3 import OrchestratorV3
from src.persistence.database_adapter import DatabaseAdapter


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Scheduler para scraping automático.
    
    Características:
    - Lee URLs activas de la BD
    - Respeta caché (no re-scrapea URLs recientes)
    - Guarda resultados automáticamente
    - Logging completo
    - Manejo robusto de errores
    """
    
    def __init__(
        self,
        db_path: str = "database/price_monitor.db",
        cache_hours: int = 24,
        headless: bool = True
    ):
        """
        Inicializa el scheduler.
        
        Args:
            db_path: Ruta a la base de datos
            cache_hours: Horas de caché (no re-scrapear)
            headless: Modo headless de Playwright
        """
        self.db_adapter = DatabaseAdapter(db_path)
        self.orchestrator = None
        self.cache_hours = cache_hours
        self.headless = headless
    
    def _init_orchestrator(self):
        """Inicializa el orchestrator si no está inicializado."""
        if not self.orchestrator:
            self.orchestrator = OrchestratorV3(headless=self.headless)
    
    def get_urls_to_scrape(self) -> List[Dict]:
        """
        Obtiene URLs que deben ser scrapeadas.
        
        Returns:
            Lista de URLs activas que no están en caché
        """
        all_urls = self.db_adapter.get_active_urls()
        logger.info(f"Total URLs activas: {len(all_urls)}")
        
        # Filtrar por caché
        urls_to_scrape = []
        for url_data in all_urls:
            url_id = url_data['id_plataforma_url']
            if self.db_adapter.should_scrape(url_id, self.cache_hours):
                urls_to_scrape.append(url_data)
            else:
                logger.debug(f"Skipping URL {url_id} (en caché)")
        
        logger.info(f"URLs a scrapear (fuera de caché): {len(urls_to_scrape)}")
        return urls_to_scrape
    
    def scrape_url(
        self,
        url_data: Dict,
        check_in: date,
        check_out: date
    ) -> Dict:
        """
        Scrapea una URL y guarda el resultado.
        
        Args:
            url_data: Dict con url, plataforma, id_plataforma_url
            check_in: Fecha check-in
            check_out: Fecha check-out
        
        Returns:
            Dict con resultado
        """
        url = url_data['url']
        platform = url_data['plataforma'].lower()
        url_id = url_data['id_plataforma_url']
        
        logger.info(f"Scraping {platform}: {url}")
        
        try:
            self._init_orchestrator()
            
            # Scraping
            result = self.orchestrator.scrape_establishment(
                platform=platform,
                url=url,
                check_in=check_in,
                check_out=check_out,
                property_id=f"{platform}_{url_id}"
            )
            
            # Agregar URL al resultado (para el adapter)
            result['url'] = url
            
            # Guardar en BD
            save_result = self.db_adapter.save_scrape_result(result)
            
            if result['status'] == 'success':
                logger.info(f"✓ {platform} URL {url_id}: {save_result['nights_saved']} noches guardadas")
            else:
                logger.warning(f"✗ {platform} URL {url_id}: {result['error']}")
            
            return {
                'url_id': url_id,
                'platform': platform,
                'status': result['status'],
                'save_status': save_result.get('status'),
                'nights_saved': save_result.get('nights_saved', 0),
                'error': result.get('error')
            }
        
        except Exception as e:
            logger.error(f"✗ Error scraping {platform} URL {url_id}: {e}")
            return {
                'url_id': url_id,
                'platform': platform,
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_all(
        self,
        days_ahead: int = 30,
        nights: int = 2,
        max_urls: int = None
    ) -> Dict:
        """
        Scrapea todas las URLs pendientes.
        
        Args:
            days_ahead: Días en el futuro para check-in
            nights: Número de noches de estadía
            max_urls: Máximo de URLs a scrapear (None = todas)
        
        Returns:
            Dict con estadísticas:
            {
                'total_urls': int,
                'success': int,
                'errors': int,
                'cached': int,
                'results': List[Dict]
            }
        """
        logger.info(f"=== Iniciando scraping scheduler V3 ===")
        logger.info(f"Parámetros: days_ahead={days_ahead}, nights={nights}, cache={self.cache_hours}h")
        
        # Fechas de búsqueda
        check_in = date.today() + timedelta(days=days_ahead)
        check_out = check_in + timedelta(days=nights)
        logger.info(f"Rango de búsqueda: {check_in} → {check_out} ({nights} noches)")
        
        # Obtener URLs a scrapear
        urls_to_scrape = self.get_urls_to_scrape()
        
        if max_urls:
            urls_to_scrape = urls_to_scrape[:max_urls]
            logger.info(f"Limitando a {max_urls} URLs")
        
        # Contadores
        stats = {
            'total_urls': len(urls_to_scrape),
            'success': 0,
            'errors': 0,
            'results': []
        }
        
        # Scrapear cada URL
        for i, url_data in enumerate(urls_to_scrape, 1):
            logger.info(f"--- URL {i}/{stats['total_urls']} ---")
            
            result = self.scrape_url(url_data, check_in, check_out)
            
            if result['status'] == 'success':
                stats['success'] += 1
            else:
                stats['errors'] += 1
            
            stats['results'].append(result)
        
        # Limpieza
        if self.orchestrator:
            self.orchestrator.cleanup()
        
        # Resumen
        logger.info(f"=== Resumen de scraping ===")
        logger.info(f"Total URLs procesadas: {stats['total_urls']}")
        logger.info(f"Éxitos: {stats['success']}")
        logger.info(f"Errores: {stats['errors']}")
        logger.info(f"Tasa de éxito: {stats['success']/stats['total_urls']*100:.1f}%" if stats['total_urls'] > 0 else "N/A")
        
        return stats
    
    def scrape_platform(
        self,
        platform: str,
        days_ahead: int = 30,
        nights: int = 2
    ) -> Dict:
        """
        Scrapea solo una plataforma específica.
        
        Args:
            platform: 'Airbnb', 'Booking', o 'Expedia'
            days_ahead: Días en el futuro
            nights: Noches de estadía
        
        Returns:
            Dict con estadísticas
        """
        all_urls = self.get_urls_to_scrape()
        platform_urls = [u for u in all_urls if u['plataforma'].lower() == platform.lower()]
        
        logger.info(f"Scraping solo {platform}: {len(platform_urls)} URLs")
        
        check_in = date.today() + timedelta(days=days_ahead)
        check_out = check_in + timedelta(days=nights)
        
        stats = {
            'platform': platform,
            'total_urls': len(platform_urls),
            'success': 0,
            'errors': 0,
            'results': []
        }
        
        for i, url_data in enumerate(platform_urls, 1):
            logger.info(f"--- {platform} URL {i}/{stats['total_urls']} ---")
            result = self.scrape_url(url_data, check_in, check_out)
            
            if result['status'] == 'success':
                stats['success'] += 1
            else:
                stats['errors'] += 1
            
            stats['results'].append(result)
        
        if self.orchestrator:
            self.orchestrator.cleanup()
        
        return stats


def main():
    """Función principal para ejecutar desde CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scheduler de scraping V3')
    parser.add_argument('--platform', type=str, help='Plataforma específica (Airbnb, Booking, Expedia)')
    parser.add_argument('--days-ahead', type=int, default=30, help='Días en el futuro para check-in')
    parser.add_argument('--nights', type=int, default=2, help='Número de noches')
    parser.add_argument('--cache-hours', type=int, default=24, help='Horas de caché')
    parser.add_argument('--max-urls', type=int, help='Máximo de URLs a procesar')
    parser.add_argument('--no-headless', action='store_true', help='Desactivar modo headless')
    
    args = parser.parse_args()
    
    # Crear scheduler
    scheduler = ScraperScheduler(
        cache_hours=args.cache_hours,
        headless=not args.no_headless
    )
    
    # Ejecutar
    if args.platform:
        stats = scheduler.scrape_platform(
            platform=args.platform,
            days_ahead=args.days_ahead,
            nights=args.nights
        )
    else:
        stats = scheduler.scrape_all(
            days_ahead=args.days_ahead,
            nights=args.nights,
            max_urls=args.max_urls
        )
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    print(f"URLs procesadas: {stats['total_urls']}")
    print(f"Éxitos: {stats['success']}")
    print(f"Errores: {stats['errors']}")
    if stats['total_urls'] > 0:
        print(f"Tasa de éxito: {stats['success']/stats['total_urls']*100:.1f}%")
    print("="*60)


if __name__ == '__main__':
    main()
