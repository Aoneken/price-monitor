"""
Configuración central de la aplicación Price-Monitor.
Carga variables de entorno desde .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# === DATABASE CONFIGURATION ===
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'database' / 'price_monitor.db'))

# === SCRAPING CONFIGURATION ===
SCRAPER_CONFIG = {
    'min_delay': int(os.getenv('SCRAPER_MIN_DELAY', 3)),
    'max_delay': int(os.getenv('SCRAPER_MAX_DELAY', 8)),
    'max_retries': int(os.getenv('SCRAPER_MAX_RETRIES', 3)),
    'headless': os.getenv('SCRAPER_HEADLESS', 'True').lower() == 'true',
}

# === DATA FRESHNESS ===
DATA_FRESHNESS_HOURS = int(os.getenv('DATA_FRESHNESS_HOURS', 48))

# === LOGGING CONFIGURATION ===
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file': os.getenv('LOG_FILE', str(BASE_DIR / 'logs' / 'scraping.log')),
}

# === PROXY CONFIGURATION (Opcional - Futuro) ===
USE_PROXY = os.getenv('USE_PROXY', 'False').lower() == 'true'
PROXY_URL = os.getenv('PROXY_URL', None)

# === PLATAFORMAS SOPORTADAS ===
SUPPORTED_PLATFORMS = ['Booking', 'Airbnb', 'Vrbo']

# === USER AGENTS (Rotación para anti-detección) ===
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# === STREAMLIT CONFIGURATION ===
STREAMLIT_CONFIG = {
    'page_title': 'Price Monitor',
    'page_icon': '📊',
    'layout': 'wide',
}
