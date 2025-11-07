"""
Utilidades para construir URLs de búsqueda con parámetros de fecha
"""
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class URLBuilder:
    """Constructor de URLs con parámetros de fecha para diferentes plataformas"""
    
    @staticmethod
    def booking_url(url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """
        Construye URL de Booking.com con parámetros de búsqueda.
        Método simplificado que funciona mejor - basado en código de rama main.
        
        Args:
            url_base: URL base del hotel en Booking
            fecha_checkin: Fecha de check-in
            noches: Número de noches
            
        Returns:
            URL completa con parámetros
            
        Ejemplo:
            Input: https://www.booking.com/hotel/es/ejemplo.html
            Output: https://www.booking.com/hotel/es/ejemplo.html?checkin=2025-12-01&checkout=2025-12-04
        """
        fecha_checkout = fecha_checkin + timedelta(days=noches)
        
        # Método simple que funciona: agregar parámetros directamente
        checkin_str = fecha_checkin.strftime('%Y-%m-%d')
        checkout_str = fecha_checkout.strftime('%Y-%m-%d')
        
        # Si la URL ya tiene parámetros, agregar con &, sino con ?
        separador = '&' if '?' in url_base else '?'
        
        url_final = f"{url_base}{separador}checkin={checkin_str}&checkout={checkout_str}&group_adults=2&no_rooms=1&group_children=0"
        
        return url_final
    
    @staticmethod
    def airbnb_url(url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """
        Construye URL de Airbnb con parámetros de búsqueda.
        Método simplificado que funciona mejor - basado en código de rama main.
        
        Args:
            url_base: URL base del listado en Airbnb
            fecha_checkin: Fecha de check-in
            noches: Número de noches
            
        Returns:
            URL completa con parámetros
            
        Ejemplo:
            Input: https://www.airbnb.com/rooms/12345678
            Output: https://www.airbnb.com/rooms/12345678?check_in=2025-12-01&check_out=2025-12-04
        """
        fecha_checkout = fecha_checkin + timedelta(days=noches)
        
        # Método simple que funciona
        checkin_str = fecha_checkin.strftime('%Y-%m-%d')
        checkout_str = fecha_checkout.strftime('%Y-%m-%d')
        
        # Si la URL ya tiene parámetros, agregar con &, sino con ?
        separador = '&' if '?' in url_base else '?'
        
        url_final = f"{url_base}{separador}check_in={checkin_str}&check_out={checkout_str}&adults=2"
        
        return url_final
    
    @staticmethod
    def vrbo_url(url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """
        Construye URL de Vrbo con parámetros de búsqueda.
        
        Args:
            url_base: URL base del listado en Vrbo
            fecha_checkin: Fecha de check-in
            noches: Número de noches
            
        Returns:
            URL completa con parámetros
        """
        fecha_checkout = fecha_checkin + timedelta(days=noches)
        
        # Método simple que funciona
        checkin_str = fecha_checkin.strftime('%Y-%m-%d')
        checkout_str = fecha_checkout.strftime('%Y-%m-%d')
        
        separador = '&' if '?' in url_base else '?'
        url_final = f"{url_base}{separador}startDate={checkin_str}&endDate={checkout_str}&adults=2"
        
        return url_final
    
    @staticmethod
    def expedia_url(url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """
        Construye URL de Expedia con parámetros de búsqueda.
        
        Args:
            url_base: URL base del hotel en Expedia
            fecha_checkin: Fecha de check-in
            noches: Número de noches
            
        Returns:
            URL completa con parámetros
            
        Ejemplo:
            Input: https://www.expedia.com/Hotel-Name.h12345.Hotel-Information
            Output: https://www.expedia.com/Hotel-Name.h12345.Hotel-Information?chkin=2025-12-01&chkout=2025-12-04
        """
        fecha_checkout = fecha_checkin + timedelta(days=noches)
        
        # Formato de Expedia: chkin y chkout en formato MM/DD/YYYY
        checkin_str = fecha_checkin.strftime('%m/%d/%Y')
        checkout_str = fecha_checkout.strftime('%m/%d/%Y')
        
        separador = '&' if '?' in url_base else '?'
        url_final = f"{url_base}{separador}chkin={checkin_str}&chkout={checkout_str}&adults=2"
        
        return url_final
