"""
Factory Pattern para crear robots de scraping dinámicamente
"""
from typing import Dict, Type
from scrapers.base_robot import BaseRobot
from scrapers.robots.booking_robot import BookingRobot
from scrapers.robots.airbnb_robot import AirbnbRobot


class PlatformNotSupportedError(Exception):
    """Excepción lanzada cuando se solicita un robot para una plataforma no soportada"""
    pass


class RobotFactory:
    """
    Factory que instancia robots según el nombre de la plataforma.
    Implementa el patrón Factory para desacoplar la creación de objetos.
    """
    
    # Registro de robots disponibles
    _robots: Dict[str, Type[BaseRobot]] = {
        'Booking': BookingRobot,
        'Airbnb': AirbnbRobot,
        # 'Vrbo': VrboRobot,  # Futuro
    }
    
    @classmethod
    def crear_robot(cls, platform_name: str) -> BaseRobot:
        """
        Crea y retorna una instancia del robot correcto.
        
        Args:
            platform_name: Nombre de la plataforma ('Booking', 'Airbnb', etc.)
            
        Returns:
            Instancia del robot específico
            
        Raises:
            PlatformNotSupportedError: Si la plataforma no está soportada
        """
        robot_class = cls._robots.get(platform_name)
        
        if robot_class is None:
            plataformas_disponibles = ', '.join(cls._robots.keys())
            raise PlatformNotSupportedError(
                f"No existe robot para '{platform_name}'. "
                f"Plataformas soportadas: {plataformas_disponibles}"
            )
        
        return robot_class()
    
    @classmethod
    def get_plataformas_soportadas(cls) -> list:
        """Retorna la lista de plataformas soportadas"""
        return list(cls._robots.keys())
    
    @classmethod
    def registrar_robot(cls, platform_name: str, robot_class: Type[BaseRobot]):
        """
        Permite registrar nuevos robots dinámicamente.
        Útil para extensiones futuras sin modificar este archivo.
        
        Args:
            platform_name: Nombre de la plataforma
            robot_class: Clase del robot (debe heredar de BaseRobot)
        """
        if not issubclass(robot_class, BaseRobot):
            raise TypeError(f"{robot_class} debe heredar de BaseRobot")
        
        cls._robots[platform_name] = robot_class
