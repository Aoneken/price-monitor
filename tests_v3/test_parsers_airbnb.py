#!/usr/bin/env python3
"""
Test suite para validar parsing de Airbnb según metodología definitiva.
Valida extracción de precio total/por noche, amenities, manejo de descuentos.
"""
import pytest
from datetime import date


class AirbnbParser:
    """Parser mínimo Airbnb para tests (prototipo)."""
    
    @staticmethod
    def parse_price_total(html_snippet: str) -> tuple[float, str]:
        """Extrae precio total y moneda de snippet HTML."""
        import re
        # Ejemplo: "$665,03 USD" o "$1.200,00 USD"
        pattern = r'[\$€]([0-9.,]+)\s*(USD|EUR|ARS)?'
        match = re.search(pattern, html_snippet)
        if not match:
            raise ValueError("Precio no encontrado")
        
        price_str = match.group(1).replace(',', '').replace('.', '')
        # Asumir últimos 2 dígitos son decimales si tiene más de 2 dígitos
        if len(price_str) > 2:
            price_float = float(price_str[:-2] + '.' + price_str[-2:])
        else:
            price_float = float(price_str)
        
        currency = match.group(2) or 'USD'
        return price_float, currency
    
    @staticmethod
    def parse_nights(html_snippet: str) -> int:
        """Extrae cantidad de noches."""
        import re
        pattern = r'por\s+(\d+)\s+noch'
        match = re.search(pattern, html_snippet, re.IGNORECASE)
        if not match:
            raise ValueError("Noches no encontrado")
        return int(match.group(1))
    
    @staticmethod
    def parse_amenities(html_snippet: str) -> dict:
        """Detecta WiFi y Desayuno (considerando <del>)."""
        import re
        # WiFi
        wifi_match = re.search(r'<del[^>]*>.*?wifi.*?</del>', html_snippet, re.I)
        wifi = 'No' if wifi_match else ('Sí' if re.search(r'\bwifi\b', html_snippet, re.I) else 'No')
        
        # Desayuno
        breakfast_match = re.search(r'<del[^>]*>.*?desayuno.*?</del>', html_snippet, re.I)
        breakfast = 'No' if breakfast_match else ('Sí' if re.search(r'\bdesayuno\b', html_snippet, re.I) else 'No')
        
        return {'wifi': wifi, 'desayuno': breakfast}
    
    @staticmethod
    def calculate_price_per_night(total: float, nights: int) -> float:
        """Calcula precio por noche."""
        if nights <= 0:
            raise ValueError("Nights must be > 0")
        return round(total / nights, 2)


class TestAirbnbParser:
    """Suite de tests para parser Airbnb."""
    
    def test_parse_price_simple(self):
        """Caso básico: precio USD."""
        html = '<span>$665,03 USD</span>'
        total, currency = AirbnbParser.parse_price_total(html)
        assert total == 665.03
        assert currency == 'USD'
    
    def test_parse_price_thousands(self):
        """Caso con miles: $1.200,00 USD."""
        html = '<span>$1.200,00 USD</span>'
        total, currency = AirbnbParser.parse_price_total(html)
        assert total == 1200.00
        assert currency == 'USD'
    
    def test_parse_nights(self):
        """Extrae número de noches."""
        html = '<span>por 2 noches</span>'
        nights = AirbnbParser.parse_nights(html)
        assert nights == 2
    
    def test_calculate_price_per_night(self):
        """Cálculo correcto por noche."""
        price_per_night = AirbnbParser.calculate_price_per_night(665.03, 2)
        # Permitir tolerancia de redondeo
        assert abs(price_per_night - 332.52) < 0.01
    
    def test_amenities_wifi_available(self):
        """WiFi disponible (no tachado)."""
        html = '<div>Wifi</div><div>Desayuno</div>'
        amenities = AirbnbParser.parse_amenities(html)
        assert amenities['wifi'] == 'Sí'
        assert amenities['desayuno'] == 'Sí'
    
    def test_amenities_wifi_unavailable(self):
        """WiFi no disponible (tachado)."""
        html = '<div><del>Wifi</del></div><div>Desayuno</div>'
        amenities = AirbnbParser.parse_amenities(html)
        assert amenities['wifi'] == 'No'
        assert amenities['desayuno'] == 'Sí'
    
    def test_amenities_none(self):
        """Sin amenities."""
        html = '<div>Cocina</div><div>Calefacción</div>'
        amenities = AirbnbParser.parse_amenities(html)
        assert amenities['wifi'] == 'No'
        assert amenities['desayuno'] == 'No'
    
    def test_price_validation_range(self):
        """Validación de rango (10-10000 por noche)."""
        price_per_night = AirbnbParser.calculate_price_per_night(20, 2)
        assert 10 <= price_per_night <= 10000
        
        with pytest.raises(ValueError):
            AirbnbParser.calculate_price_per_night(100, 0)


class TestAirbnbQuoteContract:
    """Tests de contrato de salida según metodología."""
    
    def test_quote_structure(self):
        """Validar estructura de AirbnbQuote."""
        quote = {
            'listing_id': '1413234233737891700',
            'check_in': date(2026, 1, 6),
            'check_out': date(2026, 1, 8),
            'nights': 2,
            'currency': 'USD',
            'precio_total': 665.03,
            'precio_por_noche': 332.52,
            'incluye_desayuno': 'Sí',
            'wifi_incluido': 'Sí',
            'fuente': 'dom_breakdown',
            'quality': 0.95,
        }
        
        # Validaciones
        assert quote['nights'] == (quote['check_out'] - quote['check_in']).days
        assert abs(quote['precio_total'] / quote['nights'] - quote['precio_por_noche']) < 0.01
        assert quote['incluye_desayuno'] in ['Sí', 'No']
        assert quote['wifi_incluido'] in ['Sí', 'No']
        assert 0 <= quote['quality'] <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
