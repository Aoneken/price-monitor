"""Factory para crear robots de scraping dinámicamente."""
from typing import Dict, Type

from scrapers.base_robot import BaseRobot
from scrapers.robots.booking_robot import BookingRobot
from scrapers.robots.airbnb_robot_v2 import AirbnbRobotV2
from scrapers.robots.expedia_robot import ExpediaRobot


class PlatformNotSupportedError(Exception):
    """Excepción lanzada cuando se solicita un robot para una plataforma no soportada."""
    pass


class RobotFactory:
    """Factory para instanciar robots específicos por plataforma."""

    _robots: Dict[str, Type[BaseRobot]] = {
        "Booking": BookingRobot,
        "Airbnb": AirbnbRobotV2,  # Usar versión robusta
        "Expedia": ExpediaRobot,
        # "Vrbo": VrboRobot,  # Futuro
    }

    @classmethod
    def crear_robot(cls, platform_name: str) -> BaseRobot:
        """Retorna una instancia del robot correspondiente a la plataforma."""
        robot_class = cls._robots.get(platform_name)
        if robot_class is None:
            plataformas_disponibles = ", ".join(cls._robots.keys())
            raise PlatformNotSupportedError(
                f"No existe robot para '{platform_name}'. "
                f"Plataformas soportadas: {plataformas_disponibles}"
            )
        return robot_class()

    @classmethod
    def get_plataformas_soportadas(cls) -> list[str]:
        """Retorna la lista de plataformas soportadas."""
        return list(cls._robots.keys())

    @classmethod
    def registrar_robot(cls, platform_name: str, robot_class: Type[BaseRobot]) -> None:
        """Permite registrar nuevos robots dinámicamente."""
        if not issubclass(robot_class, BaseRobot):
            raise TypeError(f"{robot_class} debe heredar de BaseRobot")
        cls._robots[platform_name] = robot_class
