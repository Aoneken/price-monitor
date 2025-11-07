"""
Database Manager (V3 Skeleton)
Solo operaciones mínimas para la tabla Establecimientos.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager
import logging

from config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestor mínimo de la base de datos para V3 (solo Establecimientos)."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Crea la base de datos y las tablas si no existen (usa schema.sql)."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # CRUD mínimos: Establecimientos
    def create_establecimiento(self, nombre: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Establecimientos (nombre_personalizado) VALUES (?)",
                (nombre,)
            )
            conn.commit()
            rid = cursor.lastrowid
            if rid is None:
                raise RuntimeError("No se pudo obtener el ID del nuevo establecimiento")
            return int(rid)

    def get_all_establecimientos(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_establecimiento, nombre_personalizado, fecha_creacion "
                "FROM Establecimientos ORDER BY nombre_personalizado"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_establecimiento_by_id(self, id_establecimiento: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM Establecimientos WHERE id_establecimiento = ?",
                (id_establecimiento,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_establecimiento(self, id_establecimiento: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM Establecimientos WHERE id_establecimiento = ?",
                (id_establecimiento,)
            )
            conn.commit()
            return cursor.rowcount > 0


# Singleton
_db_instance = None

def get_db() -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
