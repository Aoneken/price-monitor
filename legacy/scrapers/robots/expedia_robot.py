"""
Robot específico para scrapear Expedia
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import random

from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeout

from scrapers.base_robot import BaseRobot
from scrapers.utils.url_builder import URLBuilder

logger = logging.getLogger(__name__)


class ExpediaRobot(BaseRobot):
    """
    Robot para scrapear precios de Expedia.
    Implementa la lógica 3->2->1 noches y manejo de errores.
    """
    
    def __init__(self):
        super().__init__('Expedia')
        self._cargar_selectores()
    
    def _cargar_selectores(self):
        """Carga selectores desde el archivo JSON"""
        config_path = Path(__file__).parent.parent / 'config' / 'selectors.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.selectores = config.get('Expedia', {})
    
    def construir_url(self, url_base: str, fecha_checkin: datetime, noches: int) -> str:
        """Construye URL de Expedia con parámetros de búsqueda"""
        return URLBuilder.expedia_url(url_base, fecha_checkin, noches)
    
    def buscar(self, browser: Browser, url_base: str, fecha_checkin: datetime) -> Dict:
        """
        Busca precio en Expedia usando lógica 3->2->1 noches.
        
        Returns:
            Diccionario con precio, noches, detalles y error (si aplica)
        """
        intentos_noches = [3, 2, 1]
        
        for noches in intentos_noches:
            logger.info(f"[Expedia] Buscando {noches} noche(s) para {fecha_checkin.date()}")
            
            # Construir URL
            url_busqueda = self.construir_url(url_base, fecha_checkin, noches)
            logger.debug(f"[Expedia] URL: {url_busqueda}")
            
            # Crear nueva página
            context = browser.contexts[0]
            page = context.new_page()
            
            try:
                # Navegar a la URL con timeout extendido
                logger.debug(f"[Expedia] Navegando a la página...")
                page.goto(url_busqueda, wait_until='domcontentloaded', timeout=60000)
                
                # Expedia necesita tiempo para cargar JavaScript
                espera = random.randint(4000, 7000)
                logger.debug(f"[Expedia] Esperando {espera}ms para carga de JavaScript...")
                page.wait_for_timeout(espera)
                
                # Guardar screenshot para debugging
                screenshot_dir = Path(__file__).parent.parent.parent / 'debug_screenshots'
                screenshot_dir.mkdir(exist_ok=True)
                screenshot_path = screenshot_dir / f"expedia_{fecha_checkin.date()}_{noches}n.png"
                page.screenshot(path=str(screenshot_path))
                logger.debug(f"[Expedia] Screenshot guardado: {screenshot_path}")
                
                # Detectar bloqueo/CAPTCHA
                if self.detectar_bloqueo(page):
                    logger.warning("[Expedia] CAPTCHA o bloqueo detectado")
                    page.close()
                    
                    # Guardar HTML para análisis
                    html_path = screenshot_dir / f"expedia_{fecha_checkin.date()}_{noches}n_blocked.html"
                    html_content = page.content()
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    return {
                        "precio": 0,
                        "noches": 0,
                        "detalles": None,
                        "error": "CAPTCHA/Bloqueo detectado en Expedia"
                    }
                
                # Detectar si no está disponible
                if self._detectar_no_disponible(page):
                    logger.debug(f"[Expedia] No disponible para {noches} noche(s)")
                    page.close()
                    continue
                
                # Extraer precio
                precio_str = self.extraer_precio_con_selectores_alternativos(
                    page, 
                    self.selectores.get('precio', [])
                )
                
                if not precio_str:
                    logger.debug(f"[Expedia] No se encontró precio para {noches} noche(s)")
                    
                    # Guardar HTML para debugging
                    html_path = screenshot_dir / f"expedia_{fecha_checkin.date()}_{noches}n_noprice.html"
                    html_content = page.content()
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.debug(f"[Expedia] HTML guardado para análisis: {html_path}")
                    
                    page.close()
                    continue
                
                # Convertir precio
                logger.debug(f"[Expedia] Precio extraído: '{precio_str}'")
                precio_total = self.limpiar_precio(precio_str)
                
                if precio_total == 0:
                    logger.debug(f"[Expedia] Precio convertido a 0, continuando con siguiente búsqueda")
                    page.close()
                    continue
                
                # Extraer detalles
                detalles = self._extraer_detalles(page)
                
                page.close()
                
                # ¡Éxito!
                precio_por_noche = precio_total / noches
                logger.info(f"[Expedia] ✓ Precio encontrado: {precio_por_noche:.2f} ({noches} noche(s), total: {precio_total:.2f})")
                
                return {
                    "precio": round(precio_por_noche, 2),
                    "noches": noches,
                    "detalles": detalles,
                    "error": None
                }
                
            except PlaywrightTimeout:
                logger.error(f"[Expedia] Timeout navegando a {url_busqueda[:80]}...")
                page.close()
                continue
                
            except Exception as e:
                logger.error(f"[Expedia] Error inesperado: {e}", exc_info=True)
                page.close()
                continue
        
        # FRACASO TOTAL
        logger.warning("[Expedia] No disponible para ninguna duración (3, 2, 1 noches)")
        return {
            "precio": 0,
            "noches": 0,
            "detalles": None,
            "error": "No disponible (todas las búsquedas fallaron)"
        }
    
    def _detectar_no_disponible(self, page: Page) -> bool:
        """Detecta si el alojamiento no está disponible"""
        # Buscar en selectores configurados
        for selector in self.selectores.get('no_disponible', []):
            try:
                if page.locator(selector).count() > 0:
                    logger.debug(f"[Expedia] No disponible detectado con selector: {selector}")
                    return True
            except:
                continue
        
        # Buscar texto en toda la página
        try:
            contenido = page.content().lower()
            frases_no_disponible = [
                'no disponible',
                'not available',
                'sold out',
                'no hay habitaciones',
                'no rooms available',
                'fully booked'
            ]
            
            for frase in frases_no_disponible:
                if frase in contenido:
                    logger.debug(f"[Expedia] No disponible detectado por texto: '{frase}'")
                    return True
        except:
            pass
        
        return False
    
    def _extraer_detalles(self, page: Page) -> Dict[str, str]:
        """
        Extrae detalles adicionales (limpieza, impuestos, desayuno).
        
        Returns:
            Diccionario con los detalles encontrados
        """
        detalles = {
            "limpieza": "No Informa",
            "impuestos": "No Informa",
            "desayuno": "No Informa"
        }
        
        # Verificar limpieza
        for selector in self.selectores.get('limpieza_incluida', []):
            try:
                if page.locator(selector).count() > 0:
                    texto = page.locator(selector).first.inner_text().lower()
                    if 'limpieza' in texto or 'cleaning' in texto:
                        detalles["limpieza"] = "Separada" if 'fee' in texto or 'tarifa' in texto else "Incluida"
                        break
            except:
                continue
        
        # Verificar impuestos
        for selector in self.selectores.get('impuestos_incluidos', []):
            try:
                if page.locator(selector).count() > 0:
                    texto = page.locator(selector).first.inner_text().lower()
                    if 'impuesto' in texto or 'tax' in texto or 'tasa' in texto:
                        detalles["impuestos"] = "Incluidos" if 'inclui' in texto or 'included' in texto else "Separados"
                        break
            except:
                continue
        
        # Verificar desayuno
        for selector in self.selectores.get('desayuno_incluido', []):
            try:
                if page.locator(selector).count() > 0:
                    texto = page.locator(selector).first.inner_text().lower()
                    if 'desayuno' in texto or 'breakfast' in texto:
                        detalles["desayuno"] = "Incluido" if 'inclui' in texto or 'included' in texto else "Opcional"
                        break
            except:
                continue
        
        return detalles
