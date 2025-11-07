"""
Test de extracción de precio con HTML REAL de Airbnb
Usando el HTML guardado por Exequiel que muestra $254 USD por 2 noches
"""

from playwright.sync_api import sync_playwright
import sys

def extraer_precio_de_html_real():
    """
    Extrae el precio del HTML real usando diferentes estrategias
    """
    
    html_path = '/workspaces/price-monitor/debug/HTML_Exequiel.html'
    
    print("=" * 70)
    print("TEST: EXTRACCIÓN DE PRECIO CON HTML REAL DE AIRBNB")
    print("=" * 70)
    print(f"📄 Archivo: {html_path}")
    print(f"✅ Precio REAL visible: $254 USD por 2 noches")
    print(f"🎯 Objetivo: Extraer $254 correctamente\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Cargar HTML desde archivo
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        page.set_content(html_content, wait_until='domcontentloaded')
        page.wait_for_timeout(2000)  # Esperar renderizado
        
        print("=" * 70)
        print("ESTRATEGIA 1: Selectores CSS por clase específica")
        print("=" * 70)
        
        # Estrategia 1A: Clase umuerxh (precio con descuento)
        print("\n1A. Intentando selector: span.umuerxh")
        try:
            precio_elem = page.query_selector('span.umuerxh')
            if precio_elem:
                texto = precio_elem.inner_text()
                print(f"   ✅ Encontrado: '{texto}'")
            else:
                print("   ❌ No encontrado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        # Estrategia 1B: Clase s13lowb4 (precio original tachado)
        print("\n1B. Intentando selector: span.s13lowb4")
        try:
            precio_original_elem = page.query_selector('span.s13lowb4')
            if precio_original_elem:
                texto = precio_original_elem.inner_text()
                print(f"   ✅ Encontrado (precio original): '{texto}'")
            else:
                print("   ❌ No encontrado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        # Estrategia 1C: Clase q13rtw21 (texto "por 2 noches")
        print("\n1C. Intentando selector: span.q13rtw21")
        try:
            noches_elem = page.query_selector('span.q13rtw21')
            if noches_elem:
                texto = noches_elem.inner_text()
                print(f"   ✅ Encontrado: '{texto}'")
            else:
                print("   ❌ No encontrado")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        print("\n" + "=" * 70)
        print("ESTRATEGIA 2: Buscar todos los spans con atributo 'atm_'")
        print("=" * 70)
        
        spans_atm = page.query_selector_all('span[class*="atm_"]')
        print(f"\nTotal de spans con clases 'atm_': {len(spans_atm)}")
        
        precios_encontrados = []
        for idx, span in enumerate(spans_atm[:50]):  # Primeros 50 para no saturar
            texto = span.inner_text().strip()
            if texto and ('$' in texto or 'USD' in texto):
                precios_encontrados.append({
                    'index': idx,
                    'texto': texto,
                    'clase': span.get_attribute('class')
                })
        
        if precios_encontrados:
            print(f"\n✅ Encontrados {len(precios_encontrados)} spans con símbolos de precio:\n")
            for p in precios_encontrados[:10]:  # Mostrar primeros 10
                print(f"   [{p['index']}] '{p['texto']}'")
                print(f"       Clase: {p['clase'][:80]}...")  # Primeros 80 caracteres
                print()
        else:
            print("\n❌ No se encontraron spans con '$' o 'USD'")
        
        print("=" * 70)
        print("ESTRATEGIA 3: Buscar por texto usando XPath")
        print("=" * 70)
        
        # Buscar cualquier elemento que contenga "254"
        print("\n3A. Buscando elementos que contengan '254':")
        try:
            elementos_254 = page.query_selector_all("//*[contains(text(), '254')]")
            print(f"   Encontrados: {len(elementos_254)} elementos")
            for elem in elementos_254[:5]:
                tag = elem.evaluate("el => el.tagName")
                texto = elem.inner_text().strip()
                print(f"   - <{tag}>: '{texto[:100]}'")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        # Buscar "por" seguido de número
        print("\n3B. Buscando patrón 'por X noches':")
        try:
            elementos_por = page.query_selector_all("//*[contains(text(), 'por')]")
            print(f"   Encontrados: {len(elementos_por)} elementos con 'por'")
            for elem in elementos_por[:10]:
                texto = elem.inner_text().strip()
                if 'noche' in texto.lower():
                    print(f"   ✅ '{texto}'")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        
        print("\n" + "=" * 70)
        print("ESTRATEGIA 4: Buscar en el _initialData de React")
        print("=" * 70)
        
        # Airbnb usa React y suele tener los datos en un script JSON
        scripts = page.query_selector_all('script[data-hypernova-key]')
        print(f"\nScripts con data-hypernova-key: {len(scripts)}")
        
        for idx, script in enumerate(scripts[:3]):  # Revisar primeros 3
            contenido = script.inner_text()
            if 'price' in contenido.lower():
                print(f"\n   Script {idx}: Contiene 'price'")
                # Buscar números que puedan ser el precio
                import re
                precios_json = re.findall(r'"price[^"]*":\s*(\d+\.?\d*)', contenido)
                if precios_json:
                    print(f"   Precios encontrados en JSON: {precios_json[:10]}")
        
        print("\n" + "=" * 70)
        print("ESTRATEGIA 5: Selectores ACTUALES del robot")
        print("=" * 70)
        
        selectores_actuales = [
            ('span._doc79r', 'Selector actual principal'),
            ('span._tyxjp1', 'Selector actual secundario'),
            ('span[data-testid="price-item-tag"]', 'Selector por data-testid'),
            ('div[data-plugin-in-point-id="BOOK_IT_SIDEBAR"] span._tyxjp1', 'Selector con contexto'),
        ]
        
        for selector, descripcion in selectores_actuales:
            print(f"\n{descripcion}:")
            print(f"   Selector: {selector}")
            try:
                elem = page.query_selector(selector)
                if elem:
                    texto = elem.inner_text()
                    print(f"   ✅ Encontrado: '{texto}'")
                else:
                    print(f"   ❌ No encontrado")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
        
        print("\n" + "=" * 70)
        print("CONCLUSIONES")
        print("=" * 70)
        
        print("""
Si este análisis NO extrae el precio $254 USD correctamente, significa que:

1. ✅ El HTML guardado ESTÁ completo (lo viste en el navegador)
2. ❌ Los selectores CSS actuales NO funcionan con la versión nueva de Airbnb
3. 🔧 NECESITAMOS actualizar los selectores en selectors.json

Clases identificadas por Exequiel:
- umuerxh: Precio con descuento ($254 USD)
- s13lowb4: Precio original tachado ($310 USD)  
- q13rtw21: Texto "por 2 noches"

SIGUIENTE PASO:
→ Agregar estos selectores a scrapers/config/selectors.json
→ Actualizar _extraer_precio_mejorado() para probar múltiples estrategias
""")
        
        browser.close()

if __name__ == "__main__":
    try:
        extraer_precio_de_html_real()
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
