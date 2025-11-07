"""
Adapter para integrar quotes del SDK V3 con la base de datos existente.
"""
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
from pathlib import Path


class DatabaseAdapter:
    """
    Adapter para guardar quotes V3 en la base de datos legacy.
    
    Mapeo:
    - Quote V3 → Tabla Precios (por cada noche)
    - property_id debe existir en Plataformas_URL
    """
    
    def __init__(self, db_path: str = "database/price_monitor.db"):
        """
        Inicializa el adapter.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la BD."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_url_id(self, url: str) -> Optional[int]:
        """
        Obtiene el id_plataforma_url para una URL.
        
        Args:
            url: URL del establecimiento
        
        Returns:
            id_plataforma_url o None si no existe
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_plataforma_url FROM Plataformas_URL WHERE url = ?",
                (url,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def save_quote(
        self,
        quote: Dict,
        url: str,
        platform: str
    ) -> Dict:
        """
        Guarda un quote V3 en la base de datos.
        
        Args:
            quote: Quote dict del SDK V3
            url: URL del establecimiento
            platform: Plataforma ('airbnb', 'booking', 'expedia')
        
        Returns:
            Dict con resultado de la operación:
            {
                'status': 'success' | 'error',
                'url_id': int,
                'nights_saved': int,
                'error': str | None
            }
        """
        try:
            # Obtener id_plataforma_url
            url_id = self.get_url_id(url)
            if not url_id:
                return {
                    'status': 'error',
                    'url_id': None,
                    'nights_saved': 0,
                    'error': f'URL not found in database: {url}'
                }
            
            # Extraer datos del quote
            check_in = quote['check_in']
            check_out = quote['check_out']
            nights = quote['nights']
            
            # Precio por noche
            precio_por_noche = quote.get('precio_por_noche')
            if not precio_por_noche:
                return {
                    'status': 'error',
                    'url_id': url_id,
                    'nights_saved': 0,
                    'error': 'precio_por_noche not found in quote'
                }
            
            # Amenities
            incluye_desayuno = quote.get('incluye_desayuno', 'No Informa')
            wifi_incluido = quote.get('wifi_incluido', 'No')
            
            # Disponibilidad (asumimos disponible si hay precio)
            esta_ocupado = False
            
            # Timestamp del scrape
            fecha_scrape = datetime.now()
            
            # Guardar una fila por cada noche
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                nights_saved = 0
                current_date = check_in
                
                for i in range(nights):
                    # Calcular fecha de la noche
                    from datetime import timedelta
                    noche_date = current_date + timedelta(days=i)
                    
                    # Insertar/actualizar
                    cursor.execute("""
                        INSERT OR REPLACE INTO Precios (
                            id_plataforma_url,
                            fecha_noche,
                            precio_base,
                            esta_ocupado,
                            incluye_limpieza_base,
                            incluye_impuestos_base,
                            ofrece_desayuno,
                            fecha_scrape,
                            noches_encontradas,
                            error_log
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        url_id,
                        noche_date.isoformat(),
                        precio_por_noche,
                        esta_ocupado,
                        'No Informa',  # limpieza no se extrae más
                        'No Informa',  # impuestos: podríamos mapear de Booking
                        incluye_desayuno,
                        fecha_scrape,
                        nights,
                        None  # sin errores
                    ))
                    
                    nights_saved += 1
                
                conn.commit()
            
            return {
                'status': 'success',
                'url_id': url_id,
                'nights_saved': nights_saved,
                'error': None
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'url_id': None,
                'nights_saved': 0,
                'error': str(e)
            }
    
    def save_scrape_result(
        self,
        result: Dict
    ) -> Dict:
        """
        Guarda el resultado de un scraping (del orchestrator).
        
        Args:
            result: Resultado del orchestrator con:
                - status: 'success' | 'error'
                - platform: str
                - data: quote dict (si success)
                - error: str (si error)
                - url: str (debe agregarse por el caller)
        
        Returns:
            Dict con resultado de la operación
        """
        if result['status'] == 'error':
            # Guardar log de error (sin datos de precio)
            url = result.get('url')
            if not url:
                return {
                    'status': 'error',
                    'error': 'No URL provided in result'
                }
            
            url_id = self.get_url_id(url)
            if not url_id:
                return {
                    'status': 'error',
                    'error': f'URL not found: {url}'
                }
            
            # Registrar error en BD (fecha_noche = hoy, precio_base = 0)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO Precios (
                        id_plataforma_url,
                        fecha_noche,
                        precio_base,
                        esta_ocupado,
                        fecha_scrape,
                        error_log
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    url_id,
                    date.today().isoformat(),
                    0.0,
                    True,  # marcado como ocupado por error
                    datetime.now(),
                    result['error']
                ))
                conn.commit()
            
            return {
                'status': 'error_logged',
                'url_id': url_id
            }
        
        # Success: guardar quote
        quote = result['data']
        url = result.get('url')
        platform = result['platform']
        
        return self.save_quote(quote, url, platform)
    
    def get_active_urls(self) -> List[Dict]:
        """
        Obtiene todas las URLs activas de la BD.
        
        Returns:
            Lista de dicts con:
            - id_plataforma_url
            - url
            - plataforma
            - id_establecimiento
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id_plataforma_url,
                    url,
                    plataforma,
                    id_establecimiento
                FROM Plataformas_URL
                WHERE esta_activa = TRUE
                ORDER BY plataforma, id_establecimiento
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_scrapes(
        self,
        hours: int = 24
    ) -> List[Dict]:
        """
        Obtiene URLs scrapeadas recientemente.
        
        Args:
            hours: Horas hacia atrás
        
        Returns:
            Lista de id_plataforma_url scrapeados recientemente
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT id_plataforma_url
                FROM Precios
                WHERE fecha_scrape >= datetime('now', '-{} hours')
            """.format(hours))
            
            return [row[0] for row in cursor.fetchall()]
    
    def should_scrape(
        self,
        url_id: int,
        cache_hours: int = 24
    ) -> bool:
        """
        Determina si una URL debe ser scrapeada.
        
        Args:
            url_id: id_plataforma_url
            cache_hours: Horas de caché
        
        Returns:
            True si debe scrapearse, False si está en caché
        """
        recent = self.get_recent_scrapes(cache_hours)
        return url_id not in recent
