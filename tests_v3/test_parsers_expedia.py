#!/usr/bin/env python3
"""
Test suite para validar parsing de Expedia según metodología definitiva.
Valida extracción de descuentos, precio tachado, precio vigente, cálculo de porcentajes.
"""
import pytest
from datetime import date


class ExpediaParser:
    """Parser mínimo Expedia para tests (prototipo)."""
    
    @staticmethod
    def parse_price_vigente(html_snippet: str) -> tuple[float, str]:
        """Extrae precio vigente (no tachado)."""
        import re
        # Buscar precio no dentro de <del>
        pattern = r'(?<!</del>)\$([0-9.,]+)\s*en\s*total'
        match = re.search(pattern, html_snippet)
        if not match:
            raise ValueError("Precio vigente no encontrado")
        price_str = match.group(1).replace(',', '')
        return float(price_str), 'USD'
    
    @staticmethod
    def parse_price_tachado(html_snippet: str) -> float | None:
        """Extrae precio original tachado."""
        import re
        pattern = r'<del>\$([0-9.,]+)</del>'
        match = re.search(pattern, html_snippet)
        if not match:
            return None
        return float(match.group(1).replace(',', ''))
    
    @staticmethod
    def parse_descuento_badge(html_snippet: str) -> float | None:
        """Extrae monto de descuento del badge."""
        import re
        pattern = r'\$([0-9.,]+)\s*de\s*dto'
        match = re.search(pattern, html_snippet, re.I)
        if not match:
            return None
        return float(match.group(1).replace(',', ''))
    
    @staticmethod
    def parse_precio_por_noche(html_snippet: str) -> float:
        """Extrae precio por noche."""
        import re
        pattern = r'\$([0-9.,]+)\s*por\s*noche'
        match = re.search(pattern, html_snippet, re.I)
        if not match:
            raise ValueError("Precio por noche no encontrado")
        return float(match.group(1).replace(',', ''))
    
    @staticmethod
    def calculate_discount_percentage(original: float, vigente: float) -> float:
        """Calcula porcentaje de descuento."""
        if original <= 0:
            raise ValueError("Original price must be > 0")
        return round((original - vigente) / original * 100, 2)


class TestExpediaParser:
    """Suite de tests para parser Expedia."""
    
    def test_parse_price_vigente(self):
        """Precio vigente simple."""
        html = '<div>$505 en total</div>'
        price, currency = ExpediaParser.parse_price_vigente(html)
        assert price == 505.0
        assert currency == 'USD'
    
    def test_parse_price_tachado_present(self):
        """Precio original tachado."""
        html = '<div><del>$562</del></div>'
        tachado = ExpediaParser.parse_price_tachado(html)
        assert tachado == 562.0
    
    def test_parse_price_tachado_absent(self):
        """Sin precio tachado."""
        html = '<div>$505 en total</div>'
        tachado = ExpediaParser.parse_price_tachado(html)
        assert tachado is None
    
    def test_parse_descuento_badge(self):
        """Badge de descuento."""
        html = '<span>$56 de dto.</span>'
        descuento = ExpediaParser.parse_descuento_badge(html)
        assert descuento == 56.0
    
    def test_parse_precio_por_noche(self):
        """Precio por noche."""
        html = '<div>$253 por noche</div>'
        price = ExpediaParser.parse_precio_por_noche(html)
        assert price == 253.0
    
    def test_calculate_discount_percentage(self):
        """Cálculo de porcentaje de descuento."""
        percentage = ExpediaParser.calculate_discount_percentage(562, 505)
        assert abs(percentage - 10.14) < 0.1  # ~10.14%
    
    def test_discount_validation(self):
        """Validación: original > vigente."""
        with pytest.raises(ValueError):
            ExpediaParser.calculate_discount_percentage(0, 505)


class TestExpediaQuoteContract:
    """Tests de contrato ExpediaQuote."""
    
    def test_quote_structure_with_discount(self):
        """Quote con descuento."""
        quote = {
            'check_in': date(2026, 2, 14),
            'check_out': date(2026, 2, 16),
            'nights': 2,
            'currency': 'USD',
            'precio_total_vigente': 505.0,
            'precio_por_noche': 252.5,  # Corregido: 505/2 = 252.5
            'incluye_desayuno': 'No',
            'wifi_incluido': 'No',
            'precio_original_tachado': 562.0,
            'monto_descuento': 57.0,
            'porcentaje_descuento': 10.14,
            'fuente': 'dom',
            'quality': 0.9,
        }
        
        # Validaciones
        assert quote['nights'] == (quote['check_out'] - quote['check_in']).days
        assert abs(quote['precio_total_vigente'] / quote['nights'] - quote['precio_por_noche']) < 0.01
        assert quote['precio_original_tachado'] > quote['precio_total_vigente']
        assert abs(quote['monto_descuento'] - (quote['precio_original_tachado'] - quote['precio_total_vigente'])) < 0.01
        assert 0 < quote['porcentaje_descuento'] < 100
    
    def test_quote_structure_no_discount(self):
        """Quote sin descuento."""
        quote = {
            'check_in': date(2026, 1, 6),
            'check_out': date(2026, 1, 8),
            'nights': 2,
            'currency': 'USD',
            'precio_total_vigente': 600.0,
            'precio_por_noche': 300.0,
            'incluye_desayuno': 'Sí',
            'wifi_incluido': 'Sí',
            'precio_original_tachado': None,
            'monto_descuento': None,
            'porcentaje_descuento': None,
            'fuente': 'dom',
            'quality': 0.95,
        }
        
        assert quote['precio_original_tachado'] is None
        assert quote['monto_descuento'] is None
        assert quote['porcentaje_descuento'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
