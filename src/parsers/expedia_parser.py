"""
Parser para Expedia según metodología definitiva V3.
"""
import re
from datetime import date
from typing import Optional
from src.normalizers.normalizer import (
    PriceNormalizer, 
    DateNormalizer, 
    PriceValidator
)


class ExpediaParser:
    """
    Parser Expedia V3.
    Extrae precio vigente, original tachado, descuento, WiFi, Desayuno.
    """
    
    @staticmethod
    def parse_price_vigente(html: str) -> tuple[float, str]:
        """
        Extrae precio vigente (no tachado).
        
        Returns:
            (precio_vigente, currency)
        """
        # Patrón: $505 en total (no dentro de <del>)
        pattern = r'(?<!</del>)\$([0-9.,]+)\s*en\s*total'
        match = re.search(pattern, html, re.I)
        
        if not match:
            raise ValueError("EXPEDIA_PRICE_NOT_FOUND")
        
        price_str = match.group(1)
        full_str = f"${price_str}"
        precio, currency = PriceNormalizer.parse_price(full_str)
        
        return precio, currency
    
    @staticmethod
    def parse_price_tachado(html: str) -> Optional[float]:
        """
        Extrae precio original tachado (si existe).
        
        Returns:
            Precio original o None
        """
        # Patrón: <del>$562</del>
        pattern = r'<del[^>]*>\$([0-9.,]+)</del>'
        match = re.search(pattern, html, re.I)
        
        if not match:
            return None
        
        price_str = match.group(1)
        precio, _ = PriceNormalizer.parse_price(f"${price_str}")
        return precio
    
    @staticmethod
    def parse_descuento_badge(html: str) -> Optional[float]:
        """
        Extrae monto de descuento del badge.
        
        Returns:
            Monto descuento o None
        """
        # Patrón: $56 de dto.
        pattern = r'\$([0-9.,]+)\s*de\s*dto'
        match = re.search(pattern, html, re.I)
        
        if not match:
            return None
        
        desc_str = match.group(1)
        descuento, _ = PriceNormalizer.parse_price(f"${desc_str}")
        return descuento
    
    @staticmethod
    def parse_precio_por_noche(html: str) -> Optional[float]:
        """
        Extrae precio por noche del panel.
        
        Returns:
            Precio por noche o None
        """
        # Patrón: $253 por noche
        pattern = r'\$([0-9.,]+)\s*por\s*noche'
        match = re.search(pattern, html, re.I)
        
        if not match:
            return None
        
        price_str = match.group(1)
        precio, _ = PriceNormalizer.parse_price(f"${price_str}")
        return precio
    
    @staticmethod
    def parse_amenities(html: str) -> dict:
        """
        Extrae WiFi y Desayuno (básico).
        
        Returns:
            {'wifi': 'Sí'|'No', 'desayuno': 'Sí'|'No'}
        """
        wifi = 'Sí' if re.search(r'\bwifi\b|\bwi-fi\b', html, re.I) else 'No'
        desayuno = 'Sí' if re.search(r'desayuno|breakfast', html, re.I) else 'No'
        
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
        Construye ExpediaQuote completo desde HTML.
        
        Args:
            property_id: ID de la propiedad
            html: HTML del panel sticky
            check_in: Fecha check-in
            check_out: Fecha check-out
            fuente: Fuente de extracción
        
        Returns:
            ExpediaQuote dict
        """
        # Precio vigente
        precio_vigente, currency = ExpediaParser.parse_price_vigente(html)
        
        # Precio tachado (opcional)
        precio_tachado = ExpediaParser.parse_price_tachado(html)
        
        # Descuento (badge o calcular)
        descuento_badge = ExpediaParser.parse_descuento_badge(html)
        
        monto_descuento = None
        porcentaje_descuento = None
        
        if precio_tachado and precio_vigente:
            # Validar descuento
            if not PriceValidator.validate_discount(precio_tachado, precio_vigente):
                raise ValueError("EXPEDIA_DISCOUNT_AMBIGUOUS: original <= vigente")
            
            monto_descuento = round(precio_tachado - precio_vigente, 2)
            porcentaje_descuento = PriceValidator.calculate_discount_percentage(
                precio_tachado, precio_vigente
            )
        
        # Precio por noche (del panel o calcular)
        precio_por_noche_panel = ExpediaParser.parse_precio_por_noche(html)
        
        nights = DateNormalizer.validate_nights(check_in, check_out)
        
        if precio_por_noche_panel:
            precio_por_noche = precio_por_noche_panel
        else:
            precio_por_noche = PriceNormalizer.calculate_per_night(precio_vigente, nights)
        
        # Validar rango
        if not PriceValidator.validate_range(precio_por_noche):
            raise ValueError(f"PRICE_OUT_OF_RANGE: {precio_por_noche}")
        
        # Amenities
        amenities = ExpediaParser.parse_amenities(html)
        
        # Quality score
        quality = 0.9 if precio_tachado else 0.95  # Descuentos pueden ser ambiguos
        
        return {
            'property_id': property_id,
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'currency': currency,
            'precio_total_vigente': precio_vigente,
            'precio_por_noche': precio_por_noche,
            'incluye_desayuno': amenities['desayuno'],
            'wifi_incluido': amenities['wifi'],
            'precio_original_tachado': precio_tachado,
            'monto_descuento': monto_descuento,
            'porcentaje_descuento': porcentaje_descuento,
            'fuente': fuente,
            'quality': quality,
            'errores': []
        }
