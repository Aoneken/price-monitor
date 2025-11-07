"""
NUEVA ARQUITECTURA: Sistema de Extracción Robusto con Strategy Pattern
Diseñado para ser extensible y mantenible
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page, Response
import json
import re
import logging

logger = logging.getLogger(__name__)


class PriceData:
    """Estructura para datos de precio extraídos"""
    def __init__(
        self, 
        precio_total: float,
        precio_por_noche: Optional[float] = None,
        noches: Optional[int] = None,
        moneda: str = "USD",
        detalles: Optional[Dict] = None,
        fuente: str = "unknown"
    ):
        self.precio_total = precio_total
        self.precio_por_noche = precio_por_noche or (precio_total / noches if noches else precio_total)
        self.noches = noches or 1
        self.moneda = moneda
        self.detalles = detalles or {}
        self.fuente = fuente  # Para debugging: de dónde vino el dato
    
    def es_valido(self, min_price: float = 10, max_price: float = 50000) -> bool:
        """Valida que el precio esté en un rango razonable"""
        return min_price <= self.precio_total <= max_price
    
    def __repr__(self):
        return f"PriceData(${self.precio_por_noche:.2f}/noche x {self.noches}, fuente={self.fuente})"


class ExtractionStrategy(ABC):
    """Estrategia base para extracción de precios"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def extract(self, page: Page, context: Dict[str, Any]) -> Optional[PriceData]:
        """
        Intenta extraer precio usando esta estrategia
        
        Args:
            page: Página de Playwright
            context: Contexto adicional (noches esperadas, etc.)
            
        Returns:
            PriceData si tiene éxito, None si falla
        """
        pass
    
    def log_attempt(self, success: bool, message: str = ""):
        """Helper para logging consistente"""
        level = logging.INFO if success else logging.DEBUG
        status = "✓" if success else "✗"
        logger.log(level, f"[{self.name}] {status} {message}")


class NetworkAPIStrategy(ExtractionStrategy):
    """
    PRIORIDAD 1: Intercepta llamadas HTTP y extrae desde respuestas API
    Esta es LA forma más confiable cuando está disponible
    """
    
    def __init__(self):
        super().__init__("NetworkAPI")
        self.captured_responses: List[Response] = []
    
    def setup_interception(self, page: Page):
        """
        Configura interceptación de requests ANTES de navegar
        Llamar esto antes de page.goto()
        """
        def handle_response(response: Response):
            # Filtrar solo endpoints relevantes
            url = response.url.lower()
            if any(keyword in url for keyword in ['price', 'booking', 'reservation', 'availability', 'pdp']):
                self.captured_responses.append(response)
                logger.debug(f"[NetworkAPI] Capturada: {response.url[:100]}")
        
        page.on("response", handle_response)
    
    def extract(self, page: Page, context: Dict[str, Any]) -> Optional[PriceData]:
        """Busca precio en las respuestas API capturadas"""
        for response in self.captured_responses:
            try:
                if response.status != 200:
                    continue
                
                # Solo procesar JSON
                content_type = response.headers.get('content-type', '')
                if 'json' not in content_type:
                    continue
                
                # Parsear JSON
                data = response.json()
                
                # Buscar precio recursivamente
                price = self._buscar_precio_recursivo(data)
                if price:
                    self.log_attempt(True, f"Precio encontrado en {response.url[:50]}")
                    return PriceData(
                        precio_total=price,
                        noches=context.get('noches', 1),
                        fuente=f"API:{response.url[:50]}"
                    )
            
            except Exception as e:
                logger.debug(f"[NetworkAPI] Error procesando {response.url[:50]}: {e}")
                continue
        
        self.log_attempt(False, f"Sin precio en {len(self.captured_responses)} respuestas")
        return None
    
    def _buscar_precio_recursivo(self, data: Any, depth: int = 0, max_depth: int = 10) -> Optional[float]:
        """Busca campos de precio recursivamente en JSON"""
        if depth > max_depth:
            return None
        
        if isinstance(data, dict):
            # Buscar keys específicas de precio
            price_keys = ['price', 'total', 'amount', 'rate', 'cost', 'value', 'subtotal']
            for key in price_keys:
                if key in data:
                    val = data[key]
                    if isinstance(val, (int, float)) and 10 <= val <= 50000:
                        return float(val)
                    elif isinstance(val, dict):
                        # Puede ser {"amount": 150, "currency": "USD"}
                        if 'amount' in val or 'value' in val:
                            amt = val.get('amount') or val.get('value')
                            if isinstance(amt, (int, float)) and 10 <= amt <= 50000:
                                return float(amt)
            
            # Recursión en todos los valores
            for val in data.values():
                if isinstance(val, (dict, list)):
                    price = self._buscar_precio_recursivo(val, depth + 1, max_depth)
                    if price:
                        return price
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    price = self._buscar_precio_recursivo(item, depth + 1, max_depth)
                    if price:
                        return price
        
        return None


class WindowDataStrategy(ExtractionStrategy):
    """
    PRIORIDAD 2: Extrae desde datos embebidos en window (Next.js, Apollo, etc.)
    Muy confiable para SPAs modernas
    """
    
    def __init__(self):
        super().__init__("WindowData")
    
    def extract(self, page: Page, context: Dict[str, Any]) -> Optional[PriceData]:
        """Extrae precio desde window.__NEXT_DATA__ y similares"""
        
        # Estrategia 1: Next.js Data
        try:
            next_data = page.evaluate("() => window.__NEXT_DATA__")
            if next_data:
                price = self._buscar_precio_recursivo(next_data)
                if price:
                    self.log_attempt(True, "Desde window.__NEXT_DATA__")
                    return PriceData(
                        precio_total=price,
                        noches=context.get('noches', 1),
                        fuente="window.__NEXT_DATA__"
                    )
        except Exception as e:
            logger.debug(f"[WindowData] Error en __NEXT_DATA__: {e}")
        
        # Estrategia 2: Apollo State (Airbnb usa Apollo GraphQL)
        try:
            apollo_state = page.evaluate("""
                () => {
                    const elem = document.querySelector('[data-state]');
                    return elem ? elem.getAttribute('data-state') : null;
                }
            """)
            if apollo_state:
                data = json.loads(apollo_state)
                price = self._buscar_precio_recursivo(data)
                if price:
                    self.log_attempt(True, "Desde Apollo State")
                    return PriceData(
                        precio_total=price,
                        noches=context.get('noches', 1),
                        fuente="ApolloState"
                    )
        except Exception as e:
            logger.debug(f"[WindowData] Error en Apollo State: {e}")
        
        # Estrategia 3: Buscar cualquier variable global con precio
        try:
            # TODO: Implementar basado en tus hallazgos
            pass
        except Exception as e:
            logger.debug(f"[WindowData] Error buscando globals: {e}")
        
        self.log_attempt(False, "No se encontró window data")
        return None
    
    def _buscar_precio_recursivo(self, data: Any, depth: int = 0) -> Optional[float]:
        """Similar a NetworkAPIStrategy pero adaptado para window data"""
        # Reutilizar lógica
        strategy = NetworkAPIStrategy()
        return strategy._buscar_precio_recursivo(data, depth)


class DOMSelectorStrategy(ExtractionStrategy):
    """
    PRIORIDAD 3: Extracción desde DOM usando selectores CSS
    Depende de los selectores que descubras en tu inspección
    """
    
    def __init__(self, selectores: List[str]):
        super().__init__("DOMSelector")
        self.selectores = selectores
    
    def extract(self, page: Page, context: Dict[str, Any]) -> Optional[PriceData]:
        """Busca precio usando selectores CSS"""
        for selector in self.selectores:
            try:
                elementos = page.query_selector_all(selector)
                for elem in elementos:
                    texto = elem.inner_text().strip()
                    price = self._limpiar_y_validar(texto)
                    if price:
                        self.log_attempt(True, f"Selector: {selector}")
                        return PriceData(
                            precio_total=price,
                            noches=context.get('noches', 1),
                            fuente=f"DOM:{selector}"
                        )
            except Exception as e:
                logger.debug(f"[DOMSelector] Error con {selector}: {e}")
        
        self.log_attempt(False, f"Probados {len(self.selectores)} selectores")
        return None
    
    def _limpiar_y_validar(self, texto: str) -> Optional[float]:
        """Extrae número del texto y valida"""
        try:
            # Remover todo excepto dígitos y punto decimal
            numeros = re.sub(r'[^\d.]', '', texto)
            if not numeros:
                return None
            
            precio = float(numeros)
            if 10 <= precio <= 50000:
                return precio
            return None
        except:
            return None


class RegexStrategy(ExtractionStrategy):
    """
    PRIORIDAD 4: Última opción, busca con regex en todo el texto
    Menos confiable pero útil como fallback
    """
    
    def __init__(self):
        super().__init__("Regex")
    
    def extract(self, page: Page, context: Dict[str, Any]) -> Optional[PriceData]:
        """Busca precio con regex en todo el body text"""
        try:
            texto = page.inner_text('body')
            
            # Patrones priorizados
            patrones = [
                (r'\$\s*([0-9]{2,5})\s*(USD|ARS)', 'Con moneda'),
                (r'([0-9]{2,5})\s*USD\s*(?:por\s+)?noche', 'Con "por noche"'),
                (r'\$\s*([0-9]{2,5})\s*(?:por\s+)?noche', 'Con $ y noche'),
                (r'total[:\s]+\$?\s*([0-9]{2,5})', 'Con "total"'),
            ]
            
            for patron, descripcion in patrones:
                matches = re.findall(patron, texto, re.IGNORECASE)
                for match in matches:
                    try:
                        # El match puede ser tuple si hay grupos
                        numero = match[0] if isinstance(match, tuple) else match
                        precio = float(numero)
                        if 10 <= precio <= 50000:
                            self.log_attempt(True, f"{descripcion}: ${precio}")
                            return PriceData(
                                precio_total=precio,
                                noches=context.get('noches', 1),
                                fuente=f"Regex:{descripcion}"
                            )
                    except:
                        continue
            
            self.log_attempt(False, "Sin match en regex")
            return None
            
        except Exception as e:
            logger.error(f"[Regex] Error: {e}")
            return None


class RobustPriceExtractor:
    """
    Orquestador que ejecuta estrategias en orden de prioridad
    Patrón Chain of Responsibility
    """
    
    def __init__(self, strategies: List[ExtractionStrategy]):
        self.strategies = strategies
    
    def extract(self, page: Page, noches: int = 1) -> Optional[PriceData]:
        """
        Ejecuta estrategias hasta encontrar precio válido
        
        Args:
            page: Página de Playwright
            noches: Número de noches esperadas (para cálculo por noche)
            
        Returns:
            PriceData con el primer resultado válido, o None
        """
        context = {'noches': noches}
        
        for strategy in self.strategies:
            try:
                logger.info(f"[Extractor] Probando estrategia: {strategy.name}")
                result = strategy.extract(page, context)
                
                if result and result.es_valido():
                    logger.info(f"[Extractor] ✅ ÉXITO con {strategy.name}: {result}")
                    return result
                    
            except Exception as e:
                logger.error(f"[Extractor] Error en {strategy.name}: {e}")
                continue
        
        logger.warning("[Extractor] ❌ Todas las estrategias fallaron")
        return None


# ============================================================================
# FACTORY PARA CREAR EXTRACTORES CONFIGURADOS POR PLATAFORMA
# ============================================================================

def crear_extractor_airbnb(selectores_dom: Optional[List[str]] = None) -> RobustPriceExtractor:
    """
    Crea extractor específico para Airbnb
    
    Args:
        selectores_dom: Lista de selectores CSS descubiertos en inspección manual
    """
    # Selectores por defecto (serán actualizados con tus hallazgos)
    selectores = selectores_dom or [
        'span._tyxjp1',
        'span.umuerxh',
        'div[data-testid="price-summary"] span',
        # TODO: Agregar selectores reales después de inspección
    ]
    
    strategies = [
        NetworkAPIStrategy(),
        WindowDataStrategy(),
        DOMSelectorStrategy(selectores),
        RegexStrategy()
    ]
    
    return RobustPriceExtractor(strategies)


def crear_extractor_booking(selectores_dom: Optional[List[str]] = None) -> RobustPriceExtractor:
    """Crea extractor para Booking.com"""
    selectores = selectores_dom or [
        'span[data-testid="price-and-discounted-price"]',
        '.bui-price-display__value',
    ]
    
    strategies = [
        NetworkAPIStrategy(),
        WindowDataStrategy(),
        DOMSelectorStrategy(selectores),
        RegexStrategy()
    ]
    
    return RobustPriceExtractor(strategies)
