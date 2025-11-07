# 🚀 Inicio Rápido - Price Monitor

## ¿La aplicación no arranca? Sigue estos pasos:

### 1️⃣ **Método Rápido** (Recomendado)

```bash
./start.sh
```

Si ves este error: `bash: ./start.sh: Permission denied`
```bash
chmod +x start.sh stop.sh
./start.sh
```

### 2️⃣ **Método Manual**

```bash
# Opción A: Streamlit directo (bloquea el terminal)
streamlit run app.py

# Opción B: En segundo plano
nohup streamlit run app.py > logs/streamlit.log 2>&1 &
```

---

## 🌐 Acceder a la Aplicación

Una vez iniciado, abre tu navegador en:

- **Local**: http://localhost:8501
- **Network**: http://10.0.1.180:8501
- **External**: http://135.237.130.226:8501

---

## 🛑 Detener la Aplicación

```bash
./stop.sh
```

O manualmente:
```bash
pkill -f "streamlit run app.py"
```

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'streamlit'"

**Solución**: Instalar dependencias
```bash
pip install -r requirements.txt
playwright install chromium
```

### Error: "Address already in use"

**Causa**: Ya hay una instancia corriendo

**Solución**:
```bash
./stop.sh
./start.sh
```

### Error: "Database is locked"

**Causa**: SQLite no soporta múltiples escrituras simultáneas

**Solución**: Espera a que termine la operación actual o reinicia la app

### La app inicia pero no veo el menú lateral

**Causa**: Las páginas deben estar en `/pages` (raíz)

**Solución**: Ya está corregido en la última versión

---

## 📊 Verificar que Todo Funciona

### 1. Verificar que Streamlit está corriendo
```bash
ps aux | grep streamlit
```

### 2. Verificar que responde
```bash
curl http://localhost:8501
```

### 3. Ver logs en tiempo real
```bash
tail -f logs/streamlit.log
```

---

## 📁 Estructura de Archivos Clave

```
price-monitor/
├── app.py              ← Punto de entrada principal
├── pages/              ← Páginas de Streamlit (menú lateral)
│   ├── 1_Establecimientos.py
│   ├── 2_Scraping.py
│   ├── 3_Base_de_Datos.py
│   ├── 4_Dashboard.py
│   └── 5_Analisis.py
├── database/
│   └── price_monitor.db  ← Base de datos SQLite
├── logs/
│   └── streamlit.log     ← Logs de la aplicación
├── start.sh            ← Script de inicio
└── stop.sh             ← Script de detención
```

---

## ✅ Checklist de Inicio

- [ ] Dependencias instaladas: `pip list | grep streamlit`
- [ ] Chromium instalado: `playwright install chromium`
- [ ] Scripts ejecutables: `chmod +x start.sh stop.sh`
- [ ] App iniciada: `./start.sh`
- [ ] Navegador abierto: http://localhost:8501
- [ ] Menú lateral visible: 5 páginas en la izquierda

---

## 🎯 Primer Uso

1. **Abrir aplicación**: http://localhost:8501
2. **Ir a Pestaña 1**: Establecimientos
3. **Crear establecimiento**: "Mi Hotel Test"
4. **Agregar URL**: https://www.booking.com/hotel/es/[nombre-hotel].html
5. **Ir a Pestaña 2**: Scraping
6. **Ejecutar scraping**: Seleccionar establecimiento + fechas
7. **Ver resultados**: Pestaña 3 (Base de Datos) y Pestaña 4 (Dashboard)

---

## 💡 Tips

- **Logs**: `tail -f logs/streamlit.log` para debugging
- **Puerto**: Si 8501 está ocupado, Streamlit usará 8502, 8503, etc.
- **Recargar**: Ctrl+R en el navegador para recargar la app
- **Hot reload**: Streamlit recarga automáticamente al editar código

---

## 📞 Soporte

Si nada funciona:

1. Verificar Python: `python3 --version` (debe ser 3.11+)
2. Reinstalar dependencias: `pip install -r requirements.txt --force-reinstall`
3. Ver errores: `cat logs/streamlit.log`
4. Reiniciar todo: `./stop.sh && ./start.sh`

---

**Estado Actual**: ✅ La aplicación está corriendo en http://10.0.1.180:8501
