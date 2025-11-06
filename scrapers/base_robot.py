"""
Interfaz base para todos los robots de scraping (Strategy Pattern)
Todos los robots específicos deben heredar de esta clase abstracta
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
from playwright.sync_api import Page, Browser


class BaseRobot(ABC):
    """
    Clase abstracta que define la interfaz que todos los robots deben implementar.
    Esto asegura que el Orquestador pueda usar cualquier robot de forma intercambiable.
    """
    
    def __init__(self, platform_name: str):
        """
        Args:
            platform_name: Nombre de la plataforma ('Booking', 'Airbnb', etc.)
        """
        self.platform_name = platform_name
        self.selectores = {}  # Será cargado por cada robot específico
    
    @abstractmethod
    def buscar(
        self, 
        browser: Browser, 
        url_base: str, 
        fecha_checkin: datetime
    ) -> Dict:
        """
        Intenta encontrar un precio usando la lógica 3->2->1 noches.
        
        Args:
            browser: Instancia del navegador Playwright
            url_base: URL base del anuncio en la plataforma
            fecha_checkin: Fecha de check-in a buscar
            
        Returns:
            Diccionario con la estructura:
            {
                "precio": float,              # Precio por noche (0 si no disponible)
                "noches": int,                # 1, 2 o 3 (búsqueda exitosa)
                "detalles": {
                    "limpieza": str,          # 'Sí', 'No', 'No Informa'
                    "impuestos": str,         # 'Sí', 'No', 'No Informa'
                    "desayuno": str           # 'Sí', 'No', 'No Informa'
                },
                "error": Optional[str]        # Mensaje de error si hubo problemas
            }
        """
        pass
    
    @abstractmethod
    def construir_url(self, url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """
        Construye la URL completa con los parámetros de búsqueda.
        Cada plataforma tiene su propia lógica de construcción de URLs.
        
        Args:
            url_base: URL base del anuncio
            fecha_checkin: Fecha de check-in
            noches: Número de noches (1, 2 o 3)
            
        Returns:
            URL completa con parámetros de búsqueda
        """
        pass
    
    def detectar_bloqueo(self, page: Page) -> bool:
        """
        Detecta si la página muestra un CAPTCHA o mensaje de bloqueo.
        Puede ser sobrescrito por robots específicos con lógica personalizada.
        
        Args:
            page: Página de Playwright
            
        Returns:
            True si detecta bloqueo, False en caso contrario
        """
        # Selectores genéricos de bloqueo
        selectores_bloqueo = [
            "text=/verifica que eres humano/i",
            "text=/confirm you're not a robot/i",
            "text=/captcha/i",
            "#challenge-running",
            ".captcha-container"
        ]
        
        for selector in selectores_bloqueo:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        return False
    
    def extraer_precio_con_selectores_alternativos(
        self, 
        page: Page, 
        selectores: list
    ) -> Optional[str]:
        """
        Intenta extraer texto usando múltiples selectores alternativos.
        Implementa redundancia para selectores que cambian frecuentemente.
        
        Args:
            page: Página de Playwright
            selectores: Lista de selectores CSS a intentar
            
        Returns:
            Texto extraído o None si todos fallan
        """
        for selector in selectores:
            try:
                elemento = page.locator(selector).first
                if elemento.count() > 0:
                    texto = elemento.inner_text()
                    if texto:
                        return texto
            except:
                continue
        
        return None
    
    def limpiar_precio(self, precio_str: str) -> float:
        """
        Convierte una cadena de precio a float.
        Maneja diferentes formatos: "$1,234.56", "1.234,56 €", etc.
        
        Args:
            precio_str: Cadena con el precio (ej: "$1,234.56")
            
        Returns:
            Precio como float
        """
        import re
        
        # Remover símbolos de moneda y espacios
        precio_limpio = re.sub(r'[^\d,.]', '', precio_str)
        
        # Detectar formato (coma vs punto como decimal)
        if ',' in precio_limpio and '.' in precio_limpio:
            # Formato: 1.234,56 (europeo) o 1,234.56 (americano)
            if precio_limpio.rindex(',') > precio_limpio.rindex('.'):
                # Último separador es coma -> formato europeo
                precio_limpio = precio_limpio.replace('.', '').replace(',', '.')
            else:
                # Último separador es punto -> formato americano
                precio_limpio = precio_limpio.replace(',', '')
        elif ',' in precio_limpio:
            # Solo coma: podría ser decimal o miles
            if precio_limpio.count(',') == 1 and len(precio_limpio.split(',')[1]) <= 2:
                # Es decimal: 1234,56
                precio_limpio = precio_limpio.replace(',', '.')
            else:
                # Es separador de miles: 1,234
                precio_limpio = precio_limpio.replace(',', '')
        
        try:
            return float(precio_limpio)
        except:
            return 0.0
