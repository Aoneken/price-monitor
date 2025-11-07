"""
Parser para Booking según metodología definitiva V3.
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


class BookingParser:
    """
    Parser Booking V3.
    Extrae precio total + impuestos separados, WiFi gratis, Desayuno incluido.
    """
    
    @staticmethod
    def parse_price_base(html: str) -> tuple[float, str]:
        """
        Extrae precio base del resumen.
        
        Returns:
            (precio_base, currency)
        """
        # Patrón: US$323 o €450
        pattern = r'(US\$|€)([0-9.,]+)'
        match = re.search(pattern, html)
        
        if not match:
            raise ValueError("BOOKING_PRICE_NOT_FOUND")
        
        currency_symbol = match.group(1)
        price_str = match.group(2)
        
        full_str = f"{currency_symbol}{price_str}"
        precio, currency = PriceNormalizer.parse_price(full_str)
        
        return precio, currency
    
    @staticmethod
    def parse_taxes(html: str) -> Optional[float]:
        """
        Extrae impuestos/cargos adicionales si están separados.
        
        Returns:
            Monto de impuestos o None si incluidos
        """
        # Patrón: + US$147 de impuestos y cargos
        pattern = r'\+\s*(US\$|€)([0-9.,]+)\s*de\s*impuestos'
        match = re.search(pattern, html, re.I)
        
        if not match:
            return None
        
        tax_str = match.group(2)
        # Parsear número
        tax_clean = tax_str.replace(',', '')
        return float(tax_clean)
    
    @staticmethod
    def parse_amenities(html: str) -> dict:
        """
        Extrae WiFi gratis y Desayuno incluido.
        
        Returns:
            {'wifi': 'Sí'|'No', 'desayuno': 'Sí'|'No'}
        """
        # WiFi gratis (texto específico)
        wifi = 'Sí' if re.search(r'WiFi gratis', html, re.I) else 'No'
        
        # Desayuno incluido (varios formatos)
        desayuno_patterns = [
            r'desayuno.*incluido',
            r'breakfast.*included',
            r'desayuno americano incluido',
            r'bed and breakfast'
        ]
        desayuno = 'No'
        for pattern in desayuno_patterns:
            if re.search(pattern, html, re.I):
                desayuno = 'Sí'
                break
        
        return {
            'wifi': wifi,
            'desayuno': desayuno
        }
    
    @staticmethod
    def build_quote(
        property_id: str,
        html: str,
        check_in: date,
        check_out: date,
        fuente: str = 'dom'
    ) -> dict:
        """
        Construye BookingQuote completo desde HTML.
        
        Args:
            property_id: ID de la propiedad
            html: HTML del resumen
            check_in: Fecha check-in
            check_out: Fecha check-out
            fuente: Fuente de extracción
        
        Returns:
            BookingQuote dict
        """
        # Extraer precio base
        precio_base, currency = BookingParser.parse_price_base(html)
        
        # Extraer impuestos (opcional)
        impuestos = BookingParser.parse_taxes(html)
        
        # Calcular total final
        precio_total = precio_base + (impuestos or 0.0)
        
        # Calcular noches
        nights = DateNormalizer.validate_nights(check_in, check_out)
        
        # Precio por noche
        precio_por_noche = PriceNormalizer.calculate_per_night(precio_total, nights)
        
        # Validar rango
        if not PriceValidator.validate_range(precio_por_noche):
            raise ValueError(f"PRICE_OUT_OF_RANGE: {precio_por_noche}")
        
        # Amenities
        amenities = BookingParser.parse_amenities(html)
        
        # Quality score
        quality = 0.95 if fuente == 'dom' else 0.8
        
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
            'impuestos_cargos_extra': impuestos,
            'fuente': fuente,
            'quality': quality,
            'errores': []
        }
