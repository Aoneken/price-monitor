#!/usr/bin/env python3
"""
Test suite para validar parsing de Booking según metodología definitiva.
Valida extracción de precio total + impuestos, selección de habitación, amenities.
"""
import pytest
from datetime import date


class BookingParser:
    """Parser mínimo Booking para tests (prototipo)."""
    
    @staticmethod
    def parse_price_total(html_snippet: str) -> tuple[float, str]:
        """Extrae precio total base."""
        import re
        pattern = r'(US\$|€)([0-9.,]+)'
        match = re.search(pattern, html_snippet)
        if not match:
            raise ValueError("Precio no encontrado")
        
        price_str = match.group(2).replace(',', '')
        price_float = float(price_str)
        currency = 'USD' if match.group(1) == 'US$' else 'EUR'
        return price_float, currency
    
    @staticmethod
    def parse_taxes(html_snippet: str) -> float:
        """Extrae impuestos/cargos adicionales."""
        import re
        pattern = r'\+\s*(US\$|€)([0-9.,]+)\s*de\s*impuestos'
        match = re.search(pattern, html_snippet, re.IGNORECASE)
        if not match:
            return 0.0
        return float(match.group(2).replace(',', ''))
    
    @staticmethod
    def parse_amenities(html_snippet: str) -> dict:
        """Detecta WiFi gratis y Desayuno."""
        import re
        wifi = 'Sí' if re.search(r'WiFi gratis', html_snippet, re.I) else 'No'
        breakfast = 'Sí' if re.search(r'desayuno.*incluido', html_snippet, re.I) else 'No'
        return {'wifi': wifi, 'desayuno': breakfast}
    
    @staticmethod
    def calculate_final_total(base: float, taxes: float) -> float:
        """Calcula total final (base + impuestos)."""
        return round(base + taxes, 2)


class TestBookingParser:
    """Suite de tests para parser Booking."""
    
    def test_parse_price_simple(self):
        """Precio base USD."""
        html = '<span>US$323</span>'
        total, currency = BookingParser.parse_price_total(html)
        assert total == 323.0
        assert currency == 'USD'
    
    def test_parse_taxes_present(self):
        """Impuestos separados."""
        html = '<div>+ US$147 de impuestos y cargos</div>'
        taxes = BookingParser.parse_taxes(html)
        assert taxes == 147.0
    
    def test_parse_taxes_absent(self):
        """Sin impuestos separados."""
        html = '<div>Incluye impuestos y cargos</div>'
        taxes = BookingParser.parse_taxes(html)
        assert taxes == 0.0
    
    def test_calculate_final_total(self):
        """Total final = base + impuestos."""
        final = BookingParser.calculate_final_total(698.0, 147.0)
        assert final == 845.0
    
    def test_amenities_wifi_breakfast(self):
        """WiFi gratis y desayuno."""
        html = '<div>WiFi gratis</div><div>Desayuno americano incluido</div>'
        amenities = BookingParser.parse_amenities(html)
        assert amenities['wifi'] == 'Sí'
        assert amenities['desayuno'] == 'Sí'
    
    def test_amenities_none(self):
        """Sin WiFi ni desayuno."""
        html = '<div>Parking</div><div>Piscina</div>'
        amenities = BookingParser.parse_amenities(html)
        assert amenities['wifi'] == 'No'
        assert amenities['desayuno'] == 'No'


class TestBookingQuoteContract:
    """Tests de contrato BookingQuote."""
    
    def test_quote_structure_with_taxes(self):
        """Quote con impuestos separados."""
        quote = {
            'check_in': date(2026, 1, 3),
            'check_out': date(2026, 1, 4),
            'nights': 1,
            'currency': 'USD',
            'precio_total': 845.0,
            'precio_por_noche': 845.0,
            'incluye_desayuno': 'Sí',
            'wifi_incluido': 'No',
            'impuestos_cargos_extra': 147.0,
            'fuente': 'dom',
            'quality': 0.9,
        }
        
        assert quote['nights'] == (quote['check_out'] - quote['check_in']).days
        assert quote['precio_total'] == quote['precio_por_noche'] * quote['nights']
        assert quote['impuestos_cargos_extra'] > 0
    
    def test_quote_structure_no_taxes(self):
        """Quote sin impuestos separados."""
        quote = {
            'check_in': date(2025, 11, 7),
            'check_out': date(2025, 11, 9),
            'nights': 2,
            'currency': 'USD',
            'precio_total': 323.0,
            'precio_por_noche': 161.5,
            'incluye_desayuno': 'Sí',
            'wifi_incluido': 'Sí',
            'impuestos_cargos_extra': None,
            'fuente': 'dom',
            'quality': 0.95,
        }
        
        assert abs(quote['precio_total'] / quote['nights'] - quote['precio_por_noche']) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
