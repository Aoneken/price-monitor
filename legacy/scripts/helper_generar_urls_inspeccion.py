"""
HELPER: Genera URLs de test para inspección manual
"""
import sqlite3
from datetime import datetime, timedelta

def generar_urls_para_inspeccion():
    """Genera URLs listas para copiar y pegar en el navegador"""
    
    print("\n" + "="*80)
    print("URLs PARA INSPECCIÓN MANUAL")
    print("="*80)
    
    # Conectar a BD
    conn = sqlite3.connect("./database/price_monitor.db")
    cursor = conn.cursor()
    
    # Obtener URLs de Airbnb
    cursor.execute("""
        SELECT 
            e.nombre_personalizado,
            p.url,
            p.id_plataforma_url
        FROM Plataformas_URL p
        JOIN Establecimientos e ON p.id_establecimiento = e.id_establecimiento
        WHERE p.plataforma = 'Airbnb' AND p.esta_activa = TRUE
        LIMIT 5
    """)
    
    urls = cursor.fetchall()
    conn.close()
    
    if not urls:
        print("❌ No hay URLs de Airbnb configuradas")
        return
    
    # Generar fechas de prueba (diciembre 2025)
    fecha_checkin = datetime(2025, 12, 15)
    fecha_checkout = fecha_checkin + timedelta(days=3)
    
    print(f"\n📅 FECHAS SUGERIDAS:")
    print(f"   Check-in:  {fecha_checkin.strftime('%Y-%m-%d')}")
    print(f"   Check-out: {fecha_checkout.strftime('%Y-%m-%d')}")
    print(f"   Noches:    3")
    
    print(f"\n🔗 URLs PARA PROBAR EN TU NAVEGADOR:")
    print("="*80)
    
    for idx, (nombre, url_base, id_url) in enumerate(urls, 1):
        # Construir URL con parámetros
        if '?' in url_base:
            separator = '&'
        else:
            separator = '?'
        
        url_completa = (
            f"{url_base}{separator}"
            f"checkin={fecha_checkin.strftime('%Y-%m-%d')}&"
            f"checkout={fecha_checkout.strftime('%Y-%m-%d')}&"
            f"adults=2"
        )
        
        print(f"\n{idx}. {nombre}")
        print(f"   ID: {id_url}")
        print(f"   📋 URL:")
        print(f"   {url_completa}")
        print()
    
    print("="*80)
    print("\n💡 INSTRUCCIONES:")
    print("1. Copia UNA de las URLs de arriba")
    print("2. Pégala en tu navegador (Chrome/Firefox)")
    print("3. Abre DevTools (F12)")
    print("4. Sigue las instrucciones del PLAN_REFACTORIZACION.md")
    print("\n🎯 PRIORIDAD:")
    print("   - Network Tab → Buscar API con precio")
    print("   - Console → window.__NEXT_DATA__")
    print("   - Elements → Inspeccionar elemento del precio")
    print("="*80)
    
    # Generar template para respuesta
    print("\n📝 TEMPLATE PARA TU RESPUESTA:")
    print("="*80)
    print("""
## Inspección Airbnb
URL Probada: [pegar]
Establecimiento ID: [número]

### 1. DISPONIBILIDAD
- [ ] Hay precio visible: $_____ por noche
- [ ] No disponible, mensaje: "___________"

### 2. NETWORK TAB (PRIORIDAD ALTA)
¿Hay llamadas API con precio?
- [ ] Sí - Endpoint: ___________
      Copiar cURL: [pegar comando]
- [ ] No

### 3. WINDOW DATA (Console)
Ejecutar: window.__NEXT_DATA__
- [ ] Sí tiene datos
      Contiene precio: Sí/No
- [ ] No existe o error

### 4. HTML DEL PRECIO (Elements)
Selector del precio: ___________
HTML:
```html
[pegar]
```

### 5. SCREENSHOT
[adjuntar o indicar ubicación]
""")
    print("="*80)

if __name__ == "__main__":
    generar_urls_para_inspeccion()
