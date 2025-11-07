"""
Database Manager para Price-Monitor
Gestiona todas las operaciones de base de datos SQLite
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import logging

from config.settings import DATABASE_PATH, DATA_FRESHNESS_HOURS

# Configurar logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestor central de la base de datos.
    Maneja conexiones, CRUD y lógica de negocio (48h, UPSERT, etc.)
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Crea la base de datos y las tablas si no existen"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Ejecutar el schema SQL
        schema_path = Path(__file__).parent / 'schema.sql'
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info(f"Base de datos inicializada: {self.db_path}")
        else:
            logger.warning(f"Archivo schema.sql no encontrado: {schema_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexiones de base de datos.
        Asegura que las conexiones se cierren correctamente.
        
        Uso:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        try:
            yield conn
        finally:
            conn.close()
    
    # ========================================
    # CRUD: ESTABLECIMIENTOS
    # ========================================
    
    def create_establecimiento(self, nombre: str) -> int:
        """
        Crea un nuevo establecimiento.
        
        Args:
            nombre: Nombre personalizado del establecimiento
            
        Returns:
            ID del establecimiento creado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Establecimientos (nombre_personalizado) VALUES (?)",
                (nombre,)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_all_establecimientos(self) -> List[Dict]:
        """
        Obtiene todos los establecimientos.
        
        Returns:
            Lista de diccionarios con los datos de establecimientos
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_establecimiento, nombre_personalizado, fecha_creacion "
                "FROM Establecimientos ORDER BY nombre_personalizado"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_establecimiento_by_id(self, id_establecimiento: int) -> Optional[Dict]:
        """Obtiene un establecimiento por su ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Establecimientos WHERE id_establecimiento = ?",
                (id_establecimiento,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_establecimiento(self, id_establecimiento: int) -> bool:
        """
        Elimina un establecimiento (y todas sus URLs y precios por CASCADE).
        
        Returns:
            True si se eliminó, False si no existía
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM Establecimientos WHERE id_establecimiento = ?",
                (id_establecimiento,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # ========================================
    # CRUD: PLATAFORMAS_URL
    # ========================================
    
    def create_plataforma_url(self, id_establecimiento: int, plataforma: str, url: str) -> int:
        """
        Crea una nueva URL de plataforma.
        
        Args:
            id_establecimiento: ID del establecimiento al que pertenece
            plataforma: Nombre de la plataforma ('Booking', 'Airbnb', 'Vrbo')
            url: URL completa del anuncio
            
        Returns:
            ID de la URL creada
            
        Raises:
            sqlite3.IntegrityError: Si la plataforma no está soportada o la URL ya existe
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Plataformas_URL (id_establecimiento, plataforma, url) "
                "VALUES (?, ?, ?)",
                (id_establecimiento, plataforma, url)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_urls_by_establecimiento(self, id_establecimiento: int) -> List[Dict]:
        """Obtiene todas las URLs de un establecimiento"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Plataformas_URL "
                "WHERE id_establecimiento = ? "
                "ORDER BY plataforma, created_at",
                (id_establecimiento,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_urls_activas_by_establecimiento(self, id_establecimiento: int) -> List[Dict]:
        """Obtiene solo las URLs activas de un establecimiento"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Plataformas_URL "
                "WHERE id_establecimiento = ? AND esta_activa = TRUE "
                "ORDER BY plataforma",
                (id_establecimiento,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def toggle_url_activa(self, id_plataforma_url: int, activa: bool) -> bool:
        """Activa o desactiva una URL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Plataformas_URL SET esta_activa = ? WHERE id_plataforma_url = ?",
                (activa, id_plataforma_url)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_plataforma_url(self, id_plataforma_url: int) -> bool:
        """Elimina una URL (y todos sus precios por CASCADE)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM Plataformas_URL WHERE id_plataforma_url = ?",
                (id_plataforma_url,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # ========================================
    # LÓGICA DE NEGOCIO: FRESCURA 48H
    # ========================================
    
    def get_fechas_a_scrapear(
        self, 
        id_plataforma_url: int, 
        fecha_inicio: datetime, 
        fecha_fin: datetime
    ) -> List[datetime]:
        """
        Implementa la lógica de frescura de 48 horas.
        Retorna solo las fechas que necesitan ser scrapeadas:
        - Fechas que no existen en la BD
        - Fechas con datos antiguos (> 48h)
        
        Args:
            id_plataforma_url: ID de la URL a scrapear
            fecha_inicio: Fecha de inicio del rango
            fecha_fin: Fecha de fin del rango
            
        Returns:
            Lista de fechas (datetime) que necesitan scraping
        """
        # Generar todas las fechas del rango
        todas_las_fechas = []
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            todas_las_fechas.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        # Consultar datos existentes
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fecha_noche, fecha_scrape FROM Precios "
                "WHERE id_plataforma_url = ? AND fecha_noche BETWEEN ? AND ?",
                (id_plataforma_url, fecha_inicio.date(), fecha_fin.date())
            )
            datos_existentes = cursor.fetchall()
        
        # Crear set de fechas frescas (< 48h)
        ahora = datetime.now()
        umbral_frescura = timedelta(hours=DATA_FRESHNESS_HOURS)
        fechas_frescas = set()
        
        for row in datos_existentes:
            fecha_noche = datetime.strptime(str(row['fecha_noche']), '%Y-%m-%d')
            fecha_scrape = datetime.fromisoformat(row['fecha_scrape'])
            
            # Si el dato tiene menos de 48h, lo consideramos fresco
            if (ahora - fecha_scrape) < umbral_frescura:
                fechas_frescas.add(fecha_noche.date())
        
        # Filtrar: solo fechas que NO están frescas
        fechas_a_scrapear = [
            fecha for fecha in todas_las_fechas 
            if fecha.date() not in fechas_frescas
        ]
        
        return fechas_a_scrapear
    
    # ========================================
    # CRUD: PRECIOS (con UPSERT)
    # ========================================
    
    def upsert_precio(
        self,
        id_plataforma_url: int,
        fecha_noche: datetime,
        precio_base: float,
        noches_encontradas: int,
        incluye_limpieza: str = 'No Informa',
        incluye_impuestos: str = 'No Informa',
        ofrece_desayuno: str = 'No Informa',
        error_log: Optional[str] = None
    ) -> None:
        """
        Inserta o actualiza un registro de precio (UPSERT).
        Implementa la lógica de ocupación (precio=0 => ocupado=TRUE).
        
        Args:
            id_plataforma_url: ID de la URL
            fecha_noche: Fecha de la noche cotizada
            precio_base: Precio encontrado (0 si no disponible)
            noches_encontradas: 1, 2 o 3 (lógica de búsqueda que tuvo éxito)
            incluye_limpieza: 'Sí', 'No', 'No Informa'
            incluye_impuestos: 'Sí', 'No', 'No Informa'
            ofrece_desayuno: 'Sí', 'No', 'No Informa'
            error_log: Mensaje de error si hubo problemas
        """
        # Lógica de ocupación (Q19)
        esta_ocupado = (precio_base == 0)
        fecha_scrape = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Precios (
                    id_plataforma_url, fecha_noche, precio_base, esta_ocupado,
                    incluye_limpieza_base, incluye_impuestos_base, ofrece_desayuno,
                    fecha_scrape, noches_encontradas, error_log
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_plataforma_url, fecha_noche) DO UPDATE SET
                    precio_base = excluded.precio_base,
                    esta_ocupado = excluded.esta_ocupado,
                    incluye_limpieza_base = excluded.incluye_limpieza_base,
                    incluye_impuestos_base = excluded.incluye_impuestos_base,
                    ofrece_desayuno = excluded.ofrece_desayuno,
                    fecha_scrape = excluded.fecha_scrape,
                    noches_encontradas = excluded.noches_encontradas,
                    error_log = excluded.error_log
                """,
                (
                    id_plataforma_url, fecha_noche.date(), precio_base, esta_ocupado,
                    incluye_limpieza, incluye_impuestos, ofrece_desayuno,
                    fecha_scrape, noches_encontradas, error_log
                )
            )
            conn.commit()
    
    # ========================================
    # CONSULTAS: PRECIOS
    # ========================================
    
    def get_precios_by_filters(
        self,
        ids_establecimiento: Optional[List[int]] = None,
        plataformas: Optional[List[str]] = None,
        fecha_noche_inicio: Optional[datetime] = None,
        fecha_noche_fin: Optional[datetime] = None,
        fecha_scrape_inicio: Optional[datetime] = None,
        fecha_scrape_fin: Optional[datetime] = None,
        solo_ocupados: bool = False
    ) -> List[Dict]:
        """
        Consulta precios con múltiples filtros.
        Usa la vista vista_precios_completa para simplificar.
        
        Returns:
            Lista de diccionarios con todos los datos combinados
        """
        query = "SELECT * FROM vista_precios_completa WHERE 1=1"
        params = []
        
        if ids_establecimiento:
            placeholders = ','.join('?' * len(ids_establecimiento))
            query += f" AND id_establecimiento IN ({placeholders})"
            params.extend(ids_establecimiento)
        
        if plataformas:
            placeholders = ','.join('?' * len(plataformas))
            query += f" AND plataforma IN ({placeholders})"
            params.extend(plataformas)
        
        if fecha_noche_inicio:
            query += " AND fecha_noche >= ?"
            params.append(fecha_noche_inicio.date())
        
        if fecha_noche_fin:
            query += " AND fecha_noche <= ?"
            params.append(fecha_noche_fin.date())
        
        if fecha_scrape_inicio:
            query += " AND fecha_scrape >= ?"
            params.append(fecha_scrape_inicio.isoformat())
        
        if fecha_scrape_fin:
            query += " AND fecha_scrape <= ?"
            params.append(fecha_scrape_fin.isoformat())
        
        if solo_ocupados:
            query += " AND esta_ocupado = TRUE"
        
        query += " ORDER BY fecha_noche DESC, establecimiento, plataforma"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_estadisticas_establecimiento(
        self,
        id_establecimiento: int,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Dict:
        """
        Calcula estadísticas agregadas para un establecimiento.
        Usado en el Dashboard.
        
        Returns:
            Diccionario con: precio_promedio, tasa_ocupacion, total_registros, etc.
        """
        query = """
            SELECT 
                AVG(CASE WHEN precio_base > 0 THEN precio_base ELSE NULL END) as precio_promedio,
                SUM(CASE WHEN esta_ocupado = TRUE THEN 1 ELSE 0 END) as total_ocupado,
                COUNT(*) as total_registros,
                MAX(fecha_scrape) as ultimo_scrape
            FROM vista_precios_completa
            WHERE id_establecimiento = ?
        """
        params = [id_establecimiento]
        
        if fecha_inicio:
            query += " AND fecha_noche >= ?"
            params.append(fecha_inicio.date())
        
        if fecha_fin:
            query += " AND fecha_noche <= ?"
            params.append(fecha_fin.date())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                total_registros = row['total_registros'] or 0
                total_ocupado = row['total_ocupado'] or 0
                
                return {
                    'precio_promedio': round(row['precio_promedio'], 2) if row['precio_promedio'] else 0,
                    'tasa_ocupacion': round((total_ocupado / total_registros * 100), 2) if total_registros > 0 else 0,
                    'total_registros': total_registros,
                    'ultimo_scrape': row['ultimo_scrape']
                }
            
            return {
                'precio_promedio': 0,
                'tasa_ocupacion': 0,
                'total_registros': 0,
                'ultimo_scrape': None
            }
    
    # ========================================
    # ELIMINACIÓN DE DATOS
    # ========================================
    
    def delete_precios_by_filters(
        self,
        ids_establecimiento: Optional[List[int]] = None,
        plataformas: Optional[List[str]] = None,
        fecha_noche_inicio: Optional[datetime] = None,
        fecha_noche_fin: Optional[datetime] = None
    ) -> int:
        """
        Elimina registros de precios según filtros especificados.
        Útil para limpiar datos antiguos o incorrectos.
        
        Args:
            ids_establecimiento: Lista de IDs de establecimientos
            plataformas: Lista de plataformas
            fecha_noche_inicio: Fecha de inicio del rango
            fecha_noche_fin: Fecha de fin del rango
            
        Returns:
            Número de registros eliminados
            
        Raises:
            ValueError: Si no se proporciona ningún filtro (seguridad)
        """
        # SEGURIDAD: Al menos un filtro debe estar presente
        if not any([ids_establecimiento, plataformas, fecha_noche_inicio, fecha_noche_fin]):
            raise ValueError(
                "Por seguridad, debe proporcionar al menos un filtro para eliminar datos. "
                "Para eliminar todo, use delete_all_precios()."
            )
        
        # Construir query dinámicamente
        query = """
            DELETE FROM Precios 
            WHERE id_plataforma_url IN (
                SELECT id_plataforma_url FROM Plataformas_URL WHERE 1=1
        """
        params = []
        
        if ids_establecimiento:
            placeholders = ','.join('?' * len(ids_establecimiento))
            query += f" AND id_establecimiento IN ({placeholders})"
            params.extend(ids_establecimiento)
        
        if plataformas:
            placeholders = ','.join('?' * len(plataformas))
            query += f" AND plataforma IN ({placeholders})"
            params.extend(plataformas)
        
        query += ")"
        
        # Agregar filtros de fecha
        if fecha_noche_inicio:
            query += " AND fecha_noche >= ?"
            params.append(fecha_noche_inicio.date())
        
        if fecha_noche_fin:
            query += " AND fecha_noche <= ?"
            params.append(fecha_noche_fin.date())
        
        # Ejecutar eliminación
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            deleted_count = cursor.rowcount
            logger.info(f"Eliminados {deleted_count} registros de precios")
            return deleted_count
    
    def delete_all_precios(self) -> int:
        """
        Elimina TODOS los registros de precios.
        CUIDADO: Esta operación es irreversible.
        
        Returns:
            Número de registros eliminados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Precios")
            conn.commit()
            deleted_count = cursor.rowcount
            logger.warning(f"⚠️  TODOS los precios fueron eliminados: {deleted_count} registros")
            return deleted_count
    
    def count_precios_by_filters(
        self,
        ids_establecimiento: Optional[List[int]] = None,
        plataformas: Optional[List[str]] = None,
        fecha_noche_inicio: Optional[datetime] = None,
        fecha_noche_fin: Optional[datetime] = None
    ) -> int:
        """
        Cuenta registros que serían eliminados con los filtros dados.
        Útil para confirmación antes de eliminar.
        
        Args:
            ids_establecimiento: Lista de IDs de establecimientos
            plataformas: Lista de plataformas
            fecha_noche_inicio: Fecha de inicio del rango
            fecha_noche_fin: Fecha de fin del rango
            
        Returns:
            Número de registros que coinciden con los filtros
        """
        query = """
            SELECT COUNT(*) as total FROM Precios 
            WHERE id_plataforma_url IN (
                SELECT id_plataforma_url FROM Plataformas_URL WHERE 1=1
        """
        params = []
        
        if ids_establecimiento:
            placeholders = ','.join('?' * len(ids_establecimiento))
            query += f" AND id_establecimiento IN ({placeholders})"
            params.extend(ids_establecimiento)
        
        if plataformas:
            placeholders = ','.join('?' * len(plataformas))
            query += f" AND plataforma IN ({placeholders})"
            params.extend(plataformas)
        
        query += ")"
        
        if fecha_noche_inicio:
            query += " AND fecha_noche >= ?"
            params.append(fecha_noche_inicio.date())
        
        if fecha_noche_fin:
            query += " AND fecha_noche <= ?"
            params.append(fecha_noche_fin.date())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row['total'] if row else 0


# Singleton para uso global
_db_instance = None

def get_db() -> DatabaseManager:
    """Obtiene la instancia singleton del DatabaseManager"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
