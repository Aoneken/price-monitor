"""
Parser para Airbnb según metodología definitiva V3.
"""
import re
from datetime import date
from typing import Optional
from src.normalizers.normalizer import (
    PriceNormalizer, 
    DateNormalizer, 
    PriceValidator,
    AmenityNormalizer
)


class AirbnbParser:
    """
    Parser Airbnb V3.
    Extrae precio total/por noche, WiFi, Desayuno según metodología definitiva.
    """
    
    @staticmethod
    def parse_price_breakdown(html: str) -> tuple[float, str, int]:
        """
        Extrae precio total, moneda y noches del breakdown.
        Prioriza precio no tachado (vigente).
        
        Returns:
            (precio_total, currency, nights)
        """
        # Buscar precio total (no tachado)
        # Patrón: $665,03 USD o $1.200,00 USD
        price_pattern = r'(?<!</del>)[\$€]([0-9.,]+)\s*(USD|EUR|ARS)?'
        matches = re.findall(price_pattern, html, re.I)
        
        if not matches:
            raise ValueError("PRICE_NOT_FOUND: No se encontró precio en breakdown")
        
        # Tomar el primer match (precio más prominente)
        price_str = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
        currency_raw = matches[0][1] if isinstance(matches[0], tuple) and len(matches[0]) > 1 else 'USD'
        
        # Construir string completo para parser
        full_price_str = f"${price_str} {currency_raw}"
        precio_total, currency = PriceNormalizer.parse_price(full_price_str)
        
        # Extraer noches
        nights_pattern = r'por\s+(\d+)\s+noch'
        nights_match = re.search(nights_pattern, html, re.I)
        if not nights_match:
            raise ValueError("NIGHTS_NOT_FOUND: No se encontró número de noches")
        
        nights = int(nights_match.group(1))
        
        return precio_total, currency, nights
    
    @staticmethod
    def parse_amenities(html: str) -> dict:
        """
        Extrae WiFi y Desayuno (detecta elementos tachados).
        
        Returns:
            {'wifi': 'Sí'|'No', 'desayuno': 'Sí'|'No'}
        """
        wifi = AmenityNormalizer.detect_wifi(html)
        desayuno = AmenityNormalizer.detect_breakfast(html)
        
        return {
            'wifi': wifi,
            'desayuno': desayuno
        }
    
    @staticmethod
    def parse_dates(html: str) -> tuple[Optional[date], Optional[date]]:
        """
        Extrae fechas de check-in y check-out de selectores data-testid.
        
        Returns:
            (check_in, check_out) o (None, None) si no se encuentran
        """
        # Buscar data-testid="change-dates-checkIn" y checkOut
        checkin_pattern = r'data-testid="change-dates-checkIn"[^>]*>(\d+/\d+/\d+)'
        checkout_pattern = r'data-testid="change-dates-checkOut"[^>]*>(\d+/\d+/\d+)'
        
        checkin_match = re.search(checkin_pattern, html)
        checkout_match = re.search(checkout_pattern, html)
        
        if not checkin_match or not checkout_match:
            return None, None
        
        # Parsear fechas (formato: 6/1/2026 → day/month/year)
        def parse_date_str(date_str: str) -> date:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                return date(year, month, day)
            raise ValueError(f"Invalid date format: {date_str}")
        
        try:
            check_in = parse_date_str(checkin_match.group(1))
            check_out = parse_date_str(checkout_match.group(1))
            return check_in, check_out
        except Exception:
            return None, None
    
    @staticmethod
    def build_quote(
        property_id: str,
        html: str,
        check_in: date,
        check_out: date,
        fuente: str = 'dom_breakdown'
    ) -> dict:
        """
        Construye AirbnbQuote completo desde HTML.
        
        Args:
            property_id: ID de la propiedad
            html: HTML del breakdown
            check_in: Fecha check-in
            check_out: Fecha check-out
            fuente: Fuente de extracción
        
        Returns:
            AirbnbQuote dict
        """
        # Extraer datos
        precio_total, currency, nights = AirbnbParser.parse_price_breakdown(html)
        amenities = AirbnbParser.parse_amenities(html)
        
        # Calcular precio por noche
        precio_por_noche = PriceNormalizer.calculate_per_night(precio_total, nights)
        
        # Validar rango
        if not PriceValidator.validate_range(precio_por_noche):
            raise ValueError(f"PRICE_OUT_OF_RANGE: {precio_por_noche} not in [10, 10000]")
        
        # Validar nights vs fechas
        expected_nights = DateNormalizer.validate_nights(check_in, check_out)
        if expected_nights != nights:
            raise ValueError(f"NIGHTS_MISMATCH: HTML={nights}, expected={expected_nights}")
        
        # Calcular quality score (0-1)
        quality = 0.95 if fuente == 'dom_breakdown' else 0.8
        
        return {
            'property_id': property_id,
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'currency': currency,
            'precio_total': precio_total,
            'precio_por_noche': precio_por_noche,
            'incluye_desayuno': amenities['desayuno'],
            'wifi_incluido': amenities['wifi'],
            'fuente': fuente,
            'quality': quality,
            'errores': []
        }
