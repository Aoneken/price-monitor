"""
Utilidades para retry logic con exponential backoff
"""
import time
import random
from functools import wraps
from typing import Callable, Optional
import logging

from config.settings import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


def retry_con_backoff(
    max_intentos: int = SCRAPER_CONFIG['max_retries'],
    delay_base: float = 2.0,
    excepciones: tuple = (Exception,)
):
    """
    Decorador para reintentar funciones con exponential backoff.
    
    Args:
        max_intentos: Número máximo de intentos
        delay_base: Tiempo base de espera en segundos (se duplica en cada intento)
        excepciones: Tupla de excepciones a capturar
        
    Uso:
        @retry_con_backoff(max_intentos=3)
        def funcion_que_puede_fallar():
            ...
    """
    def decorador(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for intento in range(1, max_intentos + 1):
                try:
                    return func(*args, **kwargs)
                except excepciones as e:
                    if intento == max_intentos:
                        logger.error(f"{func.__name__} falló después de {max_intentos} intentos: {e}")
                        raise
                    
                    # Calcular delay con exponential backoff + jitter
                    delay = delay_base * (2 ** (intento - 1))
                    jitter = random.uniform(0, delay * 0.1)  # 10% de variación aleatoria
                    total_delay = delay + jitter
                    
                    logger.warning(
                        f"{func.__name__} falló (intento {intento}/{max_intentos}). "
                        f"Reintentando en {total_delay:.2f}s... Error: {e}"
                    )
                    time.sleep(total_delay)
            
        return wrapper
    return decorador


def esperar_aleatorio(min_segundos: Optional[float] = None, max_segundos: Optional[float] = None):
    """
    Espera un tiempo aleatorio entre min y max segundos.
    Usa configuración por defecto si no se especifican parámetros.
    
    Args:
        min_segundos: Tiempo mínimo de espera
        max_segundos: Tiempo máximo de espera
    """
    if min_segundos is None:
        min_segundos = SCRAPER_CONFIG['min_delay']
    if max_segundos is None:
        max_segundos = SCRAPER_CONFIG['max_delay']
    
    tiempo = random.uniform(min_segundos, max_segundos)
    logger.debug(f"Esperando {tiempo:.2f}s (rate limiting)")
    time.sleep(tiempo)
