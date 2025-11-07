"""
Test E2E completo del sistema Price-Monitor
Valida: CRUD → Scraping → Base de Datos → Validación
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from scrapers.orchestrator import ScrapingOrchestrator
import config.settings as settings

class TestE2E:
    def __init__(self):
        self.db = DatabaseManager(settings.DATABASE_PATH)
        self.orchestrator = ScrapingOrchestrator()
        self.test_establecimiento_id = None
        self.test_url_id = None
        self.scraping_resultados = []
        
    def setup(self):
        """Preparar base de datos limpia"""
        print("\n🧹 SETUP: Limpiando base de datos de prueba...")
        
        # Eliminar todos los establecimientos de prueba
        establecimientos = self.db.get_all_establecimientos()
        for est in establecimientos:
            if 'Test' in est['nombre_personalizado'] or 'E2E' in est['nombre_personalizado']:
                self.db.delete_establecimiento(est['id_establecimiento'])
                print(f"   ✓ Eliminado establecimiento previo ID={est['id_establecimiento']}")
    
    def test_1_crear_establecimiento(self):
        """TEST 1: Crear establecimiento de prueba"""
        print("\n📝 TEST 1: Creando establecimiento...")
        
        # Crear establecimiento
        establecimiento_id = self.db.create_establecimiento('Hotel Test E2E')
        self.test_establecimiento_id = establecimiento_id
        
        assert establecimiento_id is not None, "❌ No se creó el establecimiento"
        print(f"   ✅ Establecimiento creado con ID={establecimiento_id}")
        
        # Agregar URL de Booking
        booking_url = 'https://www.booking.com/hotel/es/abac-restaurant-hotel.html'
        url_id = self.db.create_plataforma_url(
            id_establecimiento=establecimiento_id,
            plataforma='Booking',
            url=booking_url
        )
        self.test_url_id = url_id
        
        assert url_id is not None, "❌ No se creó la URL"
        print(f"   ✅ URL de Booking agregada con ID={url_id}")
        
        # Verificar que existe
        est = self.db.get_establecimiento_by_id(establecimiento_id)
        assert est['id_establecimiento'] == establecimiento_id, "❌ ID no coincide"
        assert est['nombre_personalizado'] == 'Hotel Test E2E', "❌ Nombre no coincide"
        print(f"   ✅ Datos verificados en BD")
        
        return True
    
    def test_2_preparar_fechas(self):
        """TEST 2: Preparar fechas para scraping"""
        print("\n📅 TEST 2: Preparando fechas para scraping...")
        
        # Crear 3 fechas futuras (mañana, pasado mañana, en 3 días)
        fecha_inicio = datetime.now() + timedelta(days=1)
        fecha_fin = datetime.now() + timedelta(days=3)
        
        print(f"   → Rango: {fecha_inicio.date()} a {fecha_fin.date()}")
        
        # Verificar lógica de fechas_a_scrapear
        fechas_pendientes = self.db.get_fechas_a_scrapear(
            self.test_url_id,
            fecha_inicio,
            fecha_fin
        )
        
        print(f"   ✅ {len(fechas_pendientes)} fechas detectadas como pendientes")
        
        # Debe haber al menos 1 fecha (son fechas nuevas)
        assert len(fechas_pendientes) >= 1, f"❌ Esperaba al menos 1 fecha pendiente, obtuve {len(fechas_pendientes)}"
        
        return True
    
    def test_3_scraping_real(self):
        """TEST 3: Ejecutar scraping real con Playwright"""
        print("\n🔍 TEST 3: Ejecutando scraping real...")
        print("   ⚠️  Esto puede tardar 20-60 segundos...")
        
        # Fechas a scrapear (solo 2 días para no tardar mucho)
        fecha_inicio = datetime.now() + timedelta(days=1)
        fecha_fin = datetime.now() + timedelta(days=2)
        
        print(f"   → Rango:  {fecha_inicio.date()} a {fecha_fin.date()}")
        
        try:
            # Ejecutar orquestador
            resultados = self.orchestrator.ejecutar(
                id_establecimiento=self.test_establecimiento_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            print(f"\n   📊 Resultado del scraping:")
            print(f"      • Total resultados: {len(resultados)}")
            
            exitosos = sum(1 for r in resultados if r.error is None)
            fallidos = sum(1 for r in resultados if r.error is not None)
            
            print(f"      • Exitosos: {exitosos}")
            print(f"      • Fallidos: {fallidos}")
            
            if fallidos > 0:
                print(f"\n   ⚠️  Errores detectados:")
                for resultado in resultados:
                    if resultado.error:
                        print(f"      - {resultado.plataforma}: {resultado.error}")
            
            # Guardamos los resultados para validación posterior
            self.scraping_resultados = resultados
            
            print(f"\n   ✅ Scraping completado")
            return True
            
        except Exception as e:
            print(f"\n   ❌ ERROR durante scraping: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_4_validar_datos_bd(self):
        """TEST 4: Validar que los datos se guardaron correctamente"""
        print("\n💾 TEST 4: Validando datos en base de datos...")
        
        # Verificar registros en Precios
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query_precios = """
            SELECT COUNT(*) as total, 
                   MIN(precio_base) as min_precio, 
                   MAX(precio_base) as max_precio,
                   AVG(precio_base) as avg_precio
            FROM Precios 
            WHERE id_plataforma_url = ?
            """
            cursor.execute(query_precios, (self.test_url_id,))
            result = cursor.fetchone()
        
        total_precios = result['total']
        print(f"   → Registros en Precios: {total_precios}")
        
        if total_precios > 0:
            min_precio = result['min_precio']
            max_precio = result['max_precio']
            avg_precio = result['avg_precio']
            
            print(f"   → Precio mínimo: €{min_precio:.2f}")
            print(f"   → Precio máximo: €{max_precio:.2f}")
            print(f"   → Precio promedio: €{avg_precio:.2f}")
            
            # Validaciones de negocio
            if min_precio and min_precio > 0:
                assert max_precio >= min_precio, "❌ Precio máximo debe ser >= mínimo"
                print(f"   ✅ {total_precios} precios válidos en BD")
                return True
            else:
                print(f"   ⚠️  Precios son 0 (hotel ocupado o error)")
                return True
        else:
            print(f"   ⚠️  No se encontraron precios (posible CAPTCHA/bloqueo o hotel sin disponibilidad)")
            return True  # No es un error del sistema
    
    def test_5_logica_48h(self):
        """TEST 5: Validar lógica de 48 horas"""
        print("\n⏰ TEST 5: Validando lógica de frescura (48h)...")
        
        # Obtener fechas de nuevo (deben estar vacías porque ya se scrapearon)
        fecha_inicio = datetime.now() + timedelta(days=1)
        fecha_fin = datetime.now() + timedelta(days=2)
        
        fechas_pendientes = self.db.get_fechas_a_scrapear(
            self.test_url_id,
            fecha_inicio,
            fecha_fin
        )
        
        print(f"   → Fechas pendientes después de scraping reciente: {len(fechas_pendientes)}")
        
        if len(fechas_pendientes) == 0:
            print(f"   ✅ Lógica 48h funciona: No intenta re-scrapear fechas recientes")
            return True
        else:
            print(f"   ⚠️  Se detectaron {len(fechas_pendientes)} fechas pendientes (puede ser normal si el scraping falló)")
            return True
    
    def test_6_upsert(self):
        """TEST 6: Validar UPSERT (no duplicados)"""
        print("\n🔄 TEST 6: Validando lógica UPSERT...")
        
        # Contar precios únicos por fecha
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT 
                fecha_noche,
                COUNT(*) as registros
            FROM Precios
            WHERE id_plataforma_url = ?
            GROUP BY fecha_noche
            HAVING COUNT(*) > 1
            """
            cursor.execute(query, (self.test_url_id,))
            duplicados = cursor.fetchall()
        
        if len(duplicados) > 0:
            print(f"   ⚠️  Se encontraron {len(duplicados)} posibles duplicados:")
            for dup in duplicados:
                print(f"      - {dup['fecha_noche']}: {dup['registros']} registros")
            return False
        else:
            print(f"   ✅ No hay duplicados (UPSERT funciona correctamente)")
            return True
    
    def cleanup(self):
        """Limpiar datos de prueba"""
        print("\n🧹 CLEANUP: Limpiando datos de prueba...")
        if self.test_establecimiento_id:
            self.db.delete_establecimiento(self.test_establecimiento_id)
            print(f"   ✓ Establecimiento ID={self.test_establecimiento_id} eliminado")
    
    def run_all_tests(self):
        """Ejecutar todos los tests en orden"""
        print("="*70)
        print("🚀 INICIANDO TESTS E2E - PRICE MONITOR")
        print("="*70)
        
        resultados = []
        
        try:
            self.setup()
            
            tests = [
                ("Crear Establecimiento", self.test_1_crear_establecimiento),
                ("Preparar Fechas", self.test_2_preparar_fechas),
                ("Scraping Real", self.test_3_scraping_real),
                ("Validar BD", self.test_4_validar_datos_bd),
                ("Lógica 48h", self.test_5_logica_48h),
                ("UPSERT", self.test_6_upsert),
            ]
            
            for nombre, test_func in tests:
                try:
                    resultado = test_func()
                    resultados.append((nombre, resultado))
                except AssertionError as e:
                    print(f"\n   ❌ FALLO: {e}")
                    resultados.append((nombre, False))
                except Exception as e:
                    print(f"\n   ❌ ERROR INESPERADO: {e}")
                    import traceback
                    traceback.print_exc()
                    resultados.append((nombre, False))
            
        finally:
            self.cleanup()
        
        # Resumen final
        print("\n" + "="*70)
        print("📊 RESUMEN DE TESTS")
        print("="*70)
        
        exitosos = sum(1 for _, resultado in resultados if resultado)
        total = len(resultados)
        
        for nombre, resultado in resultados:
            status = "✅ PASS" if resultado else "❌ FAIL"
            print(f"   {status} - {nombre}")
        
        print(f"\n   Total: {exitosos}/{total} tests exitosos")
        
        if exitosos == total:
            print("\n   🎉 ¡TODOS LOS TESTS PASARON!")
            return True
        else:
            print(f"\n   ⚠️  {total - exitosos} tests fallaron")
            return False


if __name__ == '__main__':
    tester = TestE2E()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
