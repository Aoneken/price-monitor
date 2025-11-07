"""
Normalización y validación de datos extraídos.
"""
import re
from typing import Optional
from datetime import date


class PriceNormalizer:
    """Normalización de precios y monedas."""
    
    CURRENCY_MAP = {
        '$': 'USD',
        'US$': 'USD',
        '€': 'EUR',
        'EUR': 'EUR',
        'USD': 'USD',
        'ARS': 'ARS',
    }
    
    @staticmethod
    def normalize_currency(currency_str: str) -> str:
        """Normaliza símbolo o código de moneda a ISO."""
        currency_clean = currency_str.strip().upper()
        return PriceNormalizer.CURRENCY_MAP.get(currency_clean, currency_str)
    
    @staticmethod
    def parse_price(price_str: str) -> tuple[float, str]:
        """
        Extrae precio y moneda de string.
        Ejemplos:
          "$665,03 USD" → (665.03, 'USD')
          "€1.200,50" → (1200.50, 'EUR')
          "US$323" → (323.0, 'USD')
        """
        # Extraer moneda
        currency_match = re.search(r'(US\$|\$|€|EUR|USD|ARS)', price_str)
        currency = currency_match.group(1) if currency_match else 'USD'
        currency_iso = PriceNormalizer.normalize_currency(currency)
        
        # Extraer número (quitar todo menos dígitos, comas y puntos)
        number_str = re.sub(r'[^\d.,]', '', price_str)
        
        # Determinar si usa coma como decimal o separador de miles
        if ',' in number_str and '.' in number_str:
            # Ambos presentes: el último es decimal
            if number_str.rfind(',') > number_str.rfind('.'):
                # Formato europeo: 1.200,50
                number_str = number_str.replace('.', '').replace(',', '.')
            else:
                # Formato US: 1,200.50
                number_str = number_str.replace(',', '')
        elif ',' in number_str:
            # Solo coma: podría ser decimal o miles
            parts = number_str.split(',')
            if len(parts[-1]) == 2:  # Formato decimal: 665,03
                number_str = number_str.replace(',', '.')
            else:  # Separador miles: 1,200
                number_str = number_str.replace(',', '')
        
        try:
            price_float = float(number_str)
        except ValueError:
            raise ValueError(f"No se pudo parsear precio: {price_str}")
        
        return price_float, currency_iso
    
    @staticmethod
    def calculate_per_night(total: float, nights: int) -> float:
        """Calcula precio por noche con redondeo a 2 decimales."""
        if nights <= 0:
            raise ValueError("Nights must be > 0")
        return round(total / nights, 2)


class DateNormalizer:
    """Normalización de fechas."""
    
    @staticmethod
    def validate_nights(check_in: date, check_out: date) -> int:
        """Valida y calcula número de noches."""
        if check_out <= check_in:
            raise ValueError("check_out must be after check_in")
        return (check_out - check_in).days


class PriceValidator:
    """Validaciones de precios."""
    
    MIN_PRICE_PER_NIGHT = 10.0
    MAX_PRICE_PER_NIGHT = 10000.0
    
    @staticmethod
    def validate_range(price_per_night: float) -> bool:
        """Valida rango de precio por noche."""
        return PriceValidator.MIN_PRICE_PER_NIGHT <= price_per_night <= PriceValidator.MAX_PRICE_PER_NIGHT
    
    @staticmethod
    def validate_discount(original: float, vigente: float) -> bool:
        """Valida que original > vigente para descuentos."""
        return original > vigente
    
    @staticmethod
    def calculate_discount_percentage(original: float, vigente: float) -> float:
        """Calcula porcentaje de descuento."""
        if original <= 0:
            raise ValueError("Original price must be > 0")
        return round((original - vigente) / original * 100, 2)


class AmenityNormalizer:
    """Normalización de amenities."""
    
    WIFI_KEYWORDS = ['wifi', 'wi-fi', 'wi fi', 'internet']
    BREAKFAST_KEYWORDS = ['desayuno', 'breakfast', 'morning meal']
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza texto para comparación."""
        import unicodedata
        # Quitar acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        return text.lower().strip()
    
    @staticmethod
    def detect_wifi(html_or_text: str) -> str:
        """Detecta WiFi (considerando elementos tachados)."""
        text_lower = AmenityNormalizer.normalize_text(html_or_text)
        
        # Si está dentro de <del>, es No
        if re.search(r'<del[^>]*>.*?(wifi|wi-fi).*?</del>', html_or_text, re.I):
            return 'No'
        
        # Buscar keywords
        for keyword in AmenityNormalizer.WIFI_KEYWORDS:
            if keyword in text_lower:
                return 'Sí'
        return 'No'
    
    @staticmethod
    def detect_breakfast(html_or_text: str) -> str:
        """Detecta desayuno (considerando elementos tachados)."""
        text_lower = AmenityNormalizer.normalize_text(html_or_text)
        
        # Si está dentro de <del>, es No
        if re.search(r'<del[^>]*>.*?(desayuno|breakfast).*?</del>', html_or_text, re.I):
            return 'No'
        
        # Buscar keywords
        for keyword in AmenityNormalizer.BREAKFAST_KEYWORDS:
            if keyword in text_lower:
                return 'Sí'
        return 'No'
