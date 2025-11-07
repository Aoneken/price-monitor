"""
Scheduler V3 con búsqueda incremental de precios (3→2→1 noches).

Este scheduler implementa el algoritmo de búsqueda inteligente:
1. Para cada fecha, verifica caché primero
2. Si no hay caché, busca 3 noches → 2 noches → 1 noche
3. Normaliza precio_total / noches → precio_por_noche
4. Guarda precio para todas las noches cubiertas
5. Salta a la siguiente fecha no cubierta
6. Si todo falla, marca como OCUPADO ($0)
"""
import sys
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent))

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


class IncrementalScraperScheduler:
    """
    Scheduler con búsqueda incremental inteligente.
    
    Algoritmo:
    - Para cada URL y fecha_inicial:
      1. Verificar caché (saltar si existe precio reciente)
      2. Intentar 3 noches → Éxito: guardar 3 fechas, saltar +3
      3. Si falla, intentar 2 noches → Éxito: guardar 2 fechas, saltar +2
      4. Si falla, intentar 1 noche → Éxito: guardar 1 fecha, saltar +1
      5. Si todo falla: marcar OCUPADO, saltar +1
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
            cache_hours: Horas de caché
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
    
    def try_scrape_nights(
        self,
        url_data: Dict,
        fecha_inicial: date,
        nights: int
    ) -> Optional[Dict]:
        """
        Intenta scrapear con N noches.
        
        Args:
            url_data: Dict con url, plataforma, id_plataforma_url
            fecha_inicial: Fecha de check-in
            nights: Número de noches (3, 2, o 1)
        
        Returns:
            Quote dict si éxito, None si falla
        """
        url = url_data['url']
        platform = url_data['plataforma'].lower()
        url_id = url_data['id_plataforma_url']
        
        check_in = fecha_inicial
        check_out = fecha_inicial + timedelta(days=nights)
        
        logger.info(f"  Intentando {nights} noches: {check_in} → {check_out}")
        
        try:
            self._init_orchestrator()
            
            result = self.orchestrator.scrape_establishment(
                platform=platform,
                url=url,
                check_in=check_in,
                check_out=check_out,
                property_id=f"{platform}_{url_id}"
            )
            
            if result['status'] == 'success' and result['data']:
                quote = result['data']
                
                # Verificar que el precio es válido
                precio_por_noche = quote.get('precio_por_noche', 0)
                if precio_por_noche > 0:
                    logger.info(f"  ✓ {nights} noches: ${precio_por_noche}/noche (total: ${precio_por_noche * nights})")
                    return quote
                else:
                    logger.warning(f"  ✗ {nights} noches: precio inválido o 0")
                    return None
            else:
                logger.warning(f"  ✗ {nights} noches: {result.get('error', 'error desconocido')}")
                return None
        
        except Exception as e:
            logger.error(f"  ✗ {nights} noches: {str(e)}")
            return None
    
    def normalize_and_save_prices(
        self,
        url_id: int,
        fecha_inicial: date,
        quote: Dict,
        nights: int
    ) -> int:
        """
        Normaliza y guarda precios para todas las noches cubiertas.
        
        Args:
            url_id: id_plataforma_url
            fecha_inicial: Fecha de check-in
            quote: Quote dict del scraping
            nights: Número de noches scrapeadas
        
        Returns:
            Número de noches guardadas
        """
        precio_por_noche = quote['precio_por_noche']
        precio_total = precio_por_noche * nights  # O usar quote['precio_total'] si existe
        moneda = quote.get('currency', 'USD')
        incluye_desayuno = quote.get('incluye_desayuno', 'No Informa')
        wifi_incluido = quote.get('wifi_incluido', 'No')
        
        # Metadata para trazabilidad
        metadatos = {
            'intento': f"{nights}_noches",
            'check_in': quote['check_in'].isoformat(),
            'check_out': quote['check_out'].isoformat(),
            'fuente': quote.get('fuente', 'dom'),
            'quality': quote.get('quality', 0.0)
        }
        
        saved_count = 0
        
        for i in range(nights):
            fecha_noche = fecha_inicial + timedelta(days=i)
            
            success = self.db_adapter.save_price_per_night(
                url_id=url_id,
                fecha_noche=fecha_noche,
                precio=precio_por_noche,
                moneda=moneda,
                noches_scrapeadas=nights,
                precio_total_original=precio_total,
                incluye_desayuno=incluye_desayuno,
                wifi_incluido=wifi_incluido,
                esta_ocupado=False,
                metadatos=metadatos
            )
            
            if success:
                saved_count += 1
                logger.debug(f"    Guardado: {fecha_noche} → ${precio_por_noche} {moneda}")
        
        return saved_count
    
    def scrape_date_incremental(
        self,
        url_data: Dict,
        fecha_inicial: date
    ) -> Tuple[int, str]:
        """
        Scraping incremental para una fecha inicial.
        
        Algoritmo:
        1. Check cache
        2. Try 3 nights → save 3, skip +3
        3. Try 2 nights → save 2, skip +2
        4. Try 1 night  → save 1, skip +1
        5. Mark occupied → skip +1
        
        Args:
            url_data: Dict con url, plataforma, id_plataforma_url
            fecha_inicial: Fecha a procesar
        
        Returns:
            Tuple (nights_to_skip, status)
            - nights_to_skip: Cuántos días saltar para la próxima búsqueda
            - status: 'cached', 'success_3', 'success_2', 'success_1', 'occupied'
        """
        url_id = url_data['id_plataforma_url']
        
        # PASO 0: Verificar caché
        if not self.db_adapter.should_scrape_date(url_id, fecha_inicial, self.cache_hours):
            logger.info(f"  ⊙ Fecha {fecha_inicial}: en caché, omitiendo")
            return (1, 'cached')
        
        # PASO 1: Intentar 3 noches
        quote_3 = self.try_scrape_nights(url_data, fecha_inicial, nights=3)
        if quote_3:
            saved = self.normalize_and_save_prices(url_id, fecha_inicial, quote_3, nights=3)
            logger.info(f"  ✓ 3 noches guardadas ({saved}/3)")
            return (3, 'success_3')
        
        # PASO 2: Intentar 2 noches
        quote_2 = self.try_scrape_nights(url_data, fecha_inicial, nights=2)
        if quote_2:
            saved = self.normalize_and_save_prices(url_id, fecha_inicial, quote_2, nights=2)
            logger.info(f"  ✓ 2 noches guardadas ({saved}/2)")
            return (2, 'success_2')
        
        # PASO 3: Intentar 1 noche
        quote_1 = self.try_scrape_nights(url_data, fecha_inicial, nights=1)
        if quote_1:
            saved = self.normalize_and_save_prices(url_id, fecha_inicial, quote_1, nights=1)
            logger.info(f"  ✓ 1 noche guardada ({saved}/1)")
            return (1, 'success_1')
        
        # PASO 4: Marcar como OCUPADO
        logger.info(f"  🔒 Todas las búsquedas fallaron → Marcando como OCUPADO")
        self.db_adapter.mark_date_occupied(
            url_id=url_id,
            fecha_noche=fecha_inicial,
            intentos_fallidos=['3_noches', '2_noches', '1_noche']
        )
        return (1, 'occupied')
    
    def scrape_date_range(
        self,
        url_data: Dict,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Scrapea un rango de fechas con algoritmo incremental.
        
        Args:
            url_data: Dict con url, plataforma, id_plataforma_url
            start_date: Fecha inicial del rango
            end_date: Fecha final del rango (inclusive)
        
        Returns:
            Dict con estadísticas:
            {
                'total_dates': int,
                'cached': int,
                'success_3': int,
                'success_2': int,
                'success_1': int,
                'occupied': int,
                'requests_made': int,
                'efficiency': float  # % de fechas resueltas vs requests
            }
        """
        platform = url_data['plataforma']
        url_id = url_data['id_plataforma_url']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scraping {platform} URL {url_id}")
        logger.info(f"Rango: {start_date} → {end_date}")
        logger.info(f"{'='*60}")
        
        stats = {
            'total_dates': 0,
            'cached': 0,
            'success_3': 0,
            'success_2': 0,
            'success_1': 0,
            'occupied': 0,
            'requests_made': 0
        }
        
        current_date = start_date
        
        while current_date <= end_date:
            logger.info(f"\n→ Procesando fecha: {current_date}")
            
            skip_days, status = self.scrape_date_incremental(url_data, current_date)
            
            # Actualizar stats
            stats['total_dates'] += skip_days
            stats[status] += 1
            if status != 'cached':
                stats['requests_made'] += 1
            
            # Saltar días según resultado
            current_date += timedelta(days=skip_days)
        
        # Calcular eficiencia
        fechas_procesadas = sum([stats['success_3'] * 3, stats['success_2'] * 2, stats['success_1'], stats['occupied']])
        if stats['requests_made'] > 0:
            stats['efficiency'] = (fechas_procesadas / stats['requests_made']) * 100
        else:
            stats['efficiency'] = 0
        
        # Resumen
        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN - {platform} URL {url_id}")
        logger.info(f"{'='*60}")
        logger.info(f"Fechas totales:     {stats['total_dates']}")
        logger.info(f"En caché:           {stats['cached']}")
        logger.info(f"Éxitos 3 noches:    {stats['success_3']} ({stats['success_3'] * 3} fechas)")
        logger.info(f"Éxitos 2 noches:    {stats['success_2']} ({stats['success_2'] * 2} fechas)")
        logger.info(f"Éxitos 1 noche:     {stats['success_1']}")
        logger.info(f"Ocupadas:           {stats['occupied']}")
        logger.info(f"Requests hechos:    {stats['requests_made']}")
        logger.info(f"Eficiencia:         {stats['efficiency']:.1f}% (fechas/requests)")
        logger.info(f"{'='*60}\n")
        
        return stats
    
    def scrape_all_urls_date_range(
        self,
        start_date: date,
        end_date: date,
        platform_filter: Optional[str] = None,
        establishment_filter: Optional[int] = None
    ) -> Dict:
        """
        Scrapea todas las URLs activas para un rango de fechas.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            platform_filter: Filtrar por plataforma ('Airbnb', 'Booking', etc.)
            establishment_filter: Filtrar por id_establecimiento
        
        Returns:
            Dict con estadísticas globales
        """
        logger.info(f"\n{'#'*70}")
        logger.info(f"# SCRAPING INCREMENTAL V3 - INICIANDO")
        logger.info(f"#{'#'*68}")
        logger.info(f"Rango de fechas: {start_date} → {end_date}")
        logger.info(f"Caché: {self.cache_hours} horas")
        if platform_filter:
            logger.info(f"Filtro plataforma: {platform_filter}")
        if establishment_filter:
            logger.info(f"Filtro establecimiento: {establishment_filter}")
        logger.info(f"{'#'*70}\n")
        
        # Obtener URLs
        all_urls = self.db_adapter.get_active_urls()
        
        # Aplicar filtros
        if platform_filter:
            all_urls = [u for u in all_urls if u['plataforma'].lower() == platform_filter.lower()]
        
        if establishment_filter:
            all_urls = [u for u in all_urls if u['id_establecimiento'] == establishment_filter]
        
        logger.info(f"Total URLs a procesar: {len(all_urls)}\n")
        
        # Stats globales
        global_stats = {
            'total_urls': len(all_urls),
            'total_dates': 0,
            'cached': 0,
            'success_3': 0,
            'success_2': 0,
            'success_1': 0,
            'occupied': 0,
            'requests_made': 0,
            'efficiency': 0.0
        }
        
        # Procesar cada URL
        for i, url_data in enumerate(all_urls, 1):
            logger.info(f"\n[{i}/{len(all_urls)}] Procesando URL...")
            
            stats = self.scrape_date_range(url_data, start_date, end_date)
            
            # Acumular stats
            for key in ['total_dates', 'cached', 'success_3', 'success_2', 'success_1', 'occupied', 'requests_made']:
                global_stats[key] += stats[key]
        
        # Calcular eficiencia global
        fechas_procesadas = sum([
            global_stats['success_3'] * 3,
            global_stats['success_2'] * 2,
            global_stats['success_1'],
            global_stats['occupied']
        ])
        if global_stats['requests_made'] > 0:
            global_stats['efficiency'] = (fechas_procesadas / global_stats['requests_made']) * 100
        
        # Resumen global
        logger.info(f"\n{'#'*70}")
        logger.info(f"# RESUMEN GLOBAL")
        logger.info(f"#{'#'*68}")
        logger.info(f"URLs procesadas:    {global_stats['total_urls']}")
        logger.info(f"Fechas totales:     {global_stats['total_dates']}")
        logger.info(f"En caché:           {global_stats['cached']}")
        logger.info(f"Éxitos 3 noches:    {global_stats['success_3']} → {global_stats['success_3'] * 3} fechas")
        logger.info(f"Éxitos 2 noches:    {global_stats['success_2']} → {global_stats['success_2'] * 2} fechas")
        logger.info(f"Éxitos 1 noche:     {global_stats['success_1']} → {global_stats['success_1']} fechas")
        logger.info(f"Ocupadas:           {global_stats['occupied']}")
        logger.info(f"Requests totales:   {global_stats['requests_made']}")
        logger.info(f"Eficiencia global:  {global_stats['efficiency']:.1f}%")
        logger.info(f"{'#'*70}\n")
        
        # Cleanup
        if self.orchestrator:
            self.orchestrator.cleanup()
        
        return global_stats


def main():
    """Función principal para CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scheduler Incremental V3 (búsqueda 3→2→1 noches)'
    )
    parser.add_argument('--start-date', type=str, required=True, help='Fecha inicial (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='Fecha final (YYYY-MM-DD)')
    parser.add_argument('--platform', type=str, help='Filtro de plataforma (Airbnb, Booking, Expedia)')
    parser.add_argument('--establishment', type=int, help='Filtro de id_establecimiento')
    parser.add_argument('--cache-hours', type=int, default=24, help='Horas de caché (default: 24)')
    parser.add_argument('--no-headless', action='store_true', help='Desactivar modo headless')
    
    args = parser.parse_args()
    
    # Parse fechas
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    
    # Crear scheduler
    scheduler = IncrementalScraperScheduler(
        cache_hours=args.cache_hours,
        headless=not args.no_headless
    )
    
    # Ejecutar
    stats = scheduler.scrape_all_urls_date_range(
        start_date=start_date,
        end_date=end_date,
        platform_filter=args.platform,
        establishment_filter=args.establishment
    )
    
    # Mostrar resumen final
    print("\n" + "="*70)
    print("SCRAPING COMPLETADO")
    print("="*70)
    print(f"URLs:      {stats['total_urls']}")
    print(f"Fechas:    {stats['total_dates']}")
    print(f"Requests:  {stats['requests_made']}")
    print(f"Eficiencia: {stats['efficiency']:.1f}%")
    print("="*70)


if __name__ == '__main__':
    main()
