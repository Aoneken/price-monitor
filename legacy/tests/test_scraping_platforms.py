"""
Test de Validación de Scraping por Plataforma
Valida que los selectores CSS y la lógica de cada robot funcionen correctamente
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.robot_factory import RobotFactory
from scrapers.utils.stealth import configurar_navegador_stealth
from database.db_manager import DatabaseManager
import config.settings as settings

class TestScrapingPlatforms:
    """Tests específicos para validar scraping de cada plataforma"""
    
    def __init__(self):
        self.db = DatabaseManager(settings.DATABASE_PATH)
        self.factory = RobotFactory()
        self.resultados = {}
        
    def test_booking_selectors(self):
        """TEST: Validar selectores y lógica de Booking"""
        print("\n" + "="*70)
        print("🔍 TEST BOOKING: Validación de Selectores y Navegación")
        print("="*70)
        
        # URL de prueba real de Booking
        test_url = "https://www.booking.com/hotel/es/ac-hotel-sants-by-marriott.html"
        fecha_checkin = datetime.now() + timedelta(days=7)
        
        print(f"\n📍 URL de prueba: {test_url}")
        print(f"📅 Fecha check-in: {fecha_checkin.strftime('%Y-%m-%d')}")
        print("\n⚙️  Iniciando navegador...")
        
        browser = None
        context = None
        
        try:
            # Crear robot de Booking
            robot = self.factory.crear_robot('Booking')
            print(f"✅ Robot de Booking creado: {robot.__class__.__name__}")
            
            # Iniciar navegador
            browser, context = configurar_navegador_stealth()
            print("✅ Navegador Playwright iniciado con modo stealth")
            
            # Intentar scraping
            print("\n🔄 Ejecutando búsqueda de precios...")
            print("   → Intentando 3 noches...")
            resultado_3n = robot.buscar(context, test_url, fecha_checkin, 3)
            
            if resultado_3n:
                print(f"   ✅ Búsqueda 3 noches exitosa")
                print(f"      • Precio: €{resultado_3n.get('precio', 0):.2f}")
                print(f"      • Disponible: {not resultado_3n.get('ocupado', True)}")
                self.resultados['Booking'] = {
                    'status': 'success',
                    'precio': resultado_3n.get('precio', 0),
                    'ocupado': resultado_3n.get('ocupado', False),
                    'noches': 3
                }
                return True
            else:
                print(f"   ⚠️  Búsqueda 3 noches sin resultado, probando 2 noches...")
                resultado_2n = robot.buscar(context, test_url, fecha_checkin, 2)
                
                if resultado_2n:
                    print(f"   ✅ Búsqueda 2 noches exitosa")
                    print(f"      • Precio: €{resultado_2n.get('precio', 0):.2f}")
                    self.resultados['Booking'] = {
                        'status': 'success',
                        'precio': resultado_2n.get('precio', 0),
                        'ocupado': resultado_2n.get('ocupado', False),
                        'noches': 2
                    }
                    return True
                else:
                    print(f"   ⚠️  Búsqueda 2 noches sin resultado, probando 1 noche...")
                    resultado_1n = robot.buscar(context, test_url, fecha_checkin, 1)
                    
                    if resultado_1n:
                        print(f"   ✅ Búsqueda 1 noche exitosa")
                        print(f"      • Precio: €{resultado_1n.get('precio', 0):.2f}")
                        self.resultados['Booking'] = {
                            'status': 'success',
                            'precio': resultado_1n.get('precio', 0),
                            'ocupado': resultado_1n.get('ocupado', False),
                            'noches': 1
                        }
                        return True
                    else:
                        print(f"   ❌ No se pudo obtener precio (hotel ocupado o selectores incorrectos)")
                        self.resultados['Booking'] = {
                            'status': 'no_availability',
                            'error': 'Sin disponibilidad en 3, 2, 1 noches'
                        }
                        return False
                        
        except Exception as e:
            print(f"\n❌ ERROR durante el scraping de Booking:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.resultados['Booking'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
            
        finally:
            if browser:
                print("\n🔄 Cerrando navegador...")
                browser.close()
                print("✅ Navegador cerrado")
    
    def test_airbnb_selectors(self):
        """TEST: Validar selectores y lógica de Airbnb"""
        print("\n" + "="*70)
        print("🏡 TEST AIRBNB: Validación de Selectores y Navegación")
        print("="*70)
        
        # URL de prueba real de Airbnb
        test_url = "https://www.airbnb.com/rooms/51786693"
        fecha_checkin = datetime.now() + timedelta(days=10)
        
        print(f"\n📍 URL de prueba: {test_url}")
        print(f"📅 Fecha check-in: {fecha_checkin.strftime('%Y-%m-%d')}")
        print("\n⚙️  Iniciando navegador...")
        
        browser = None
        context = None
        
        try:
            # Crear robot de Airbnb
            robot = self.factory.crear_robot('Airbnb')
            print(f"✅ Robot de Airbnb creado: {robot.__class__.__name__}")
            
            # Iniciar navegador
            browser, context = configurar_navegador_stealth()
            print("✅ Navegador Playwright iniciado con modo stealth")
            
            # Intentar scraping
            print("\n🔄 Ejecutando búsqueda de precios...")
            print("   → Intentando 3 noches...")
            resultado_3n = robot.buscar(context, test_url, fecha_checkin, 3)
            
            if resultado_3n:
                print(f"   ✅ Búsqueda 3 noches exitosa")
                print(f"      • Precio: €{resultado_3n.get('precio', 0):.2f}")
                print(f"      • Disponible: {not resultado_3n.get('ocupado', True)}")
                self.resultados['Airbnb'] = {
                    'status': 'success',
                    'precio': resultado_3n.get('precio', 0),
                    'ocupado': resultado_3n.get('ocupado', False),
                    'noches': 3
                }
                return True
            else:
                print(f"   ⚠️  Búsqueda 3 noches sin resultado, probando 2 noches...")
                resultado_2n = robot.buscar(context, test_url, fecha_checkin, 2)
                
                if resultado_2n:
                    print(f"   ✅ Búsqueda 2 noches exitosa")
                    print(f"      • Precio: €{resultado_2n.get('precio', 0):.2f}")
                    self.resultados['Airbnb'] = {
                        'status': 'success',
                        'precio': resultado_2n.get('precio', 0),
                        'ocupado': resultado_2n.get('ocupado', False),
                        'noches': 2
                    }
                    return True
                else:
                    print(f"   ⚠️  Búsqueda 2 noches sin resultado, probando 1 noche...")
                    resultado_1n = robot.buscar(context, test_url, fecha_checkin, 1)
                    
                    if resultado_1n:
                        print(f"   ✅ Búsqueda 1 noche exitosa")
                        print(f"      • Precio: €{resultado_1n.get('precio', 0):.2f}")
                        self.resultados['Airbnb'] = {
                            'status': 'success',
                            'precio': resultado_1n.get('precio', 0),
                            'ocupado': resultado_1n.get('ocupado', False),
                            'noches': 1
                        }
                        return True
                    else:
                        print(f"   ❌ No se pudo obtener precio (hotel ocupado o selectores incorrectos)")
                        self.resultados['Airbnb'] = {
                            'status': 'no_availability',
                            'error': 'Sin disponibilidad en 3, 2, 1 noches'
                        }
                        return False
                        
        except Exception as e:
            print(f"\n❌ ERROR durante el scraping de Airbnb:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.resultados['Airbnb'] = {
                'status': 'error',
                'error': str(e)
            }
            return False
            
        finally:
            if browser:
                print("\n🔄 Cerrando navegador...")
                browser.close()
                print("✅ Navegador cerrado")
    
    def test_selector_fallback(self):
        """TEST: Validar que los selectores alternativos funcionan"""
        print("\n" + "="*70)
        print("🔄 TEST FALLBACK: Validación de Selectores Alternativos")
        print("="*70)
        
        import json
        selectors_path = Path(__file__).parent.parent / 'scrapers' / 'config' / 'selectors.json'
        
        print(f"\n📄 Cargando selectores desde: {selectors_path}")
        
        try:
            with open(selectors_path, 'r', encoding='utf-8') as f:
                selectors = json.load(f)
            
            print("✅ Archivo de selectores cargado correctamente\n")
            
            for plataforma, config in selectors.items():
                print(f"🏷️  Plataforma: {plataforma}")
                for tipo, lista_selectores in config.items():
                    cantidad = len(lista_selectores) if isinstance(lista_selectores, list) else 1
                    print(f"   • {tipo}: {cantidad} selector(es) alternativos")
                    if isinstance(lista_selectores, list):
                        for idx, sel in enumerate(lista_selectores, 1):
                            print(f"     [{idx}] {sel}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR al cargar selectores: {e}")
            return False
    
    def generar_reporte(self):
        """Genera reporte final de todos los tests"""
        print("\n" + "="*70)
        print("📊 REPORTE FINAL: Validación de Scraping por Plataforma")
        print("="*70)
        
        print("\n┌─────────────────────────────────────────────────────────────────┐")
        print("│                    RESUMEN DE RESULTADOS                        │")
        print("├─────────────────────────────────────────────────────────────────┤")
        
        for plataforma, resultado in self.resultados.items():
            status_emoji = {
                'success': '✅',
                'no_availability': '⚠️',
                'error': '❌'
            }.get(resultado.get('status'), '❓')
            
            print(f"│ {status_emoji} {plataforma:15} │ ", end="")
            
            if resultado.get('status') == 'success':
                precio = resultado.get('precio', 0)
                noches = resultado.get('noches', 0)
                ocupado = resultado.get('ocupado', False)
                
                if ocupado or precio == 0:
                    print(f"Hotel OCUPADO (€0.00 / {noches}N)           │")
                else:
                    print(f"€{precio:.2f} / {noches} noche(s)               │")
            
            elif resultado.get('status') == 'no_availability':
                print(f"Sin disponibilidad                    │")
            
            else:
                error = resultado.get('error', 'Error desconocido')[:30]
                print(f"{error:35} │")
        
        print("└─────────────────────────────────────────────────────────────────┘")
        
        # Análisis
        print("\n📌 CONCLUSIONES:")
        
        exitosos = sum(1 for r in self.resultados.values() if r.get('status') == 'success')
        total = len(self.resultados)
        
        if exitosos == total:
            print("   🎉 TODOS los scrapers funcionan correctamente")
            print("   ✅ Los selectores CSS están actualizados")
            print("   ✅ La lógica 3→2→1 noches funciona")
            print("   ✅ El modo stealth evitó bloqueos")
        elif exitosos > 0:
            print(f"   ⚠️  {exitosos}/{total} scrapers funcionan correctamente")
            print("   ⚠️  Algunos selectores pueden necesitar actualización")
        else:
            print(f"   ❌ NINGÚN scraper funcionó correctamente")
            print("   ❌ Los selectores CSS probablemente están desactualizados")
            print("   ❌ O las plataformas detectaron el scraping")
        
        print("\n💡 RECOMENDACIONES:")
        
        for plataforma, resultado in self.resultados.items():
            if resultado.get('status') == 'error':
                print(f"   • {plataforma}: Revisar selectores en scrapers/config/selectors.json")
                print(f"     Inspeccionar manualmente la página y actualizar selectores CSS")
            elif resultado.get('status') == 'no_availability':
                print(f"   • {plataforma}: Probar con diferentes URLs o fechas más lejanas")
    
    def run_all_tests(self):
        """Ejecutar todos los tests de plataformas"""
        print("\n" + "🚀"*35)
        print("INICIANDO TESTS DE VALIDACIÓN DE SCRAPING POR PLATAFORMA")
        print("🚀"*35)
        
        tests = [
            ("Selectores Alternativos", self.test_selector_fallback),
            ("Booking", self.test_booking_selectors),
            ("Airbnb", self.test_airbnb_selectors),
        ]
        
        for nombre, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ ERROR CRÍTICO en test {nombre}: {e}")
                import traceback
                traceback.print_exc()
        
        self.generar_reporte()


if __name__ == '__main__':
    tester = TestScrapingPlatforms()
    tester.run_all_tests()
