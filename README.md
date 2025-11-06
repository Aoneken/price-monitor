# 💰 Price Monitor - Airbnb vs Booking

Sistema de monitoreo y comparación de precios entre plataformas de alojamiento (Airbnb y Booking.com).

## 🚀 Características

- **Scraping Automatizado**: Extrae precios de Airbnb y Booking para rangos de fechas
- **Comparación Visual**: Gráficos interactivos para analizar diferencias de precios
- **Interfaz Web**: Aplicación Streamlit intuitiva y fácil de usar
- **Análisis Estadístico**: Métricas y estadísticas de precios por plataforma
- **Exportación**: Guarda datos en CSV y exporta a Excel
- **Escalable**: Fácil de agregar más propiedades y plataformas

## 📋 Requisitos Previos

- Python 3.8 o superior
- Google Chrome o Chromium instalado
- Conexión a Internet

## 🔧 Instalación

1. **Clonar el repositorio** (o ya estás en el Codespace):
```bash
cd /workspaces/price-monitor
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Instalar navegadores de Playwright**:
```bash
playwright install chromium
```

## ⚙️ Configuración

### Configurar Propiedades Competidoras

Edita el archivo `config/competitors.json` para agregar tus propiedades:

```json
{
  "properties": [
    {
      "name": "Nombre de tu Propiedad",
      "platforms": {
        "airbnb": "URL_COMPLETA_DE_AIRBNB",
        "booking": "URL_COMPLETA_DE_BOOKING"
      }
    }
  ]
}
```

**Ejemplo con tus URLs**:
```json
{
  "properties": [
    {
      "name": "Aizeder Eco Container House",
      "platforms": {
        "airbnb": "https://www.airbnb.com.ar/rooms/928978094650118177",
        "booking": "https://www.booking.com/hotel/ar/aizeder-eco-container-house.es.html"
      }
    }
  ]
}
```

## 🎮 Uso

### Iniciar la Aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador (generalmente en `http://localhost:8501`).

### Workflow Típico

1. **Seleccionar Propiedad**: En el sidebar, elige la propiedad que quieres monitorear
2. **Configurar Fechas**: 
   - Fecha de inicio
   - Fecha de fin
   - Noches por reserva
   - Número de huéspedes
3. **Seleccionar Plataformas**: Elige Airbnb, Booking, o ambas
4. **▶️ PLAY**: Presiona el botón para iniciar el scraping
5. **Ver Resultados**: Analiza los gráficos y estadísticas
6. **Exportar**: Descarga los datos a Excel si lo necesitas

### Modo Histórico

- Cambia a "📊 Ver Datos Históricos" en el sidebar
- Visualiza todos los datos recopilados anteriormente
- Compara precios a lo largo del tiempo
- Analiza tendencias y patrones

## 📁 Estructura del Proyecto

```
price-monitor/
├── app.py                      # Aplicación principal Streamlit
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── config/
│   └── competitors.json        # Configuración de propiedades
├── src/
│   ├── airbnb_scraper.py      # Scraper de Airbnb
│   ├── booking_scraper.py     # Scraper de Booking
│   ├── data_manager.py        # Gestión de datos
│   └── visualizer.py          # Visualizaciones
└── data/
    ├── price_history.csv      # Datos históricos (se genera automáticamente)
    └── *.xlsx                 # Exportaciones Excel
```

## 📊 Visualizaciones Incluidas

1. **Comparación de Precios**: Gráfico de líneas mostrando precios por fecha
2. **Diferencia de Precios**: Barras mostrando cuándo una plataforma es más barata
3. **Distribución de Precios**: Histogramas y box plots por plataforma
4. **Tabla de Estadísticas**: Min, Max, Promedio, Mediana por plataforma

## 🛠️ Solución de Problemas

### El scraping no obtiene precios

- **Causa**: Los selectores CSS de las páginas pueden cambiar
- **Solución**: Actualiza los selectores en `airbnb_scraper.py` o `booking_scraper.py`

### Error al instalar Playwright

```bash
# Linux/Ubuntu
sudo apt-get install -y libgbm1 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

# Luego instalar navegadores
playwright install chromium
```

### La aplicación no encuentra los módulos

Asegúrate de ejecutar desde el directorio raíz:
```bash
cd /workspaces/price-monitor
streamlit run app.py
```

## 🔮 Futuras Mejoras

- [ ] Soporte para más plataformas (VRBO, Expedia, etc.)
- [ ] Notificaciones cuando los precios bajen
- [ ] API REST para integración con otros sistemas
- [ ] Scraping programado (cron jobs)
- [ ] Base de datos SQL en lugar de CSV
- [ ] Predicción de precios con ML
- [ ] Soporte multi-moneda

## 📝 Notas Importantes

⚠️ **Web Scraping Legal**: Este proyecto es para uso educativo y personal. Asegúrate de:
- Respetar los términos de servicio de las plataformas
- No saturar los servidores con requests excesivos
- Usar los datos de manera responsable

⚠️ **Rate Limiting**: El scraper incluye pausas entre requests (2 segundos) para no saturar los servidores.

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Algunas ideas:
- Mejorar los selectores CSS para mayor precisión
- Agregar más plataformas
- Mejorar las visualizaciones
- Optimizar el rendimiento

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👤 Autor

Desarrollado para monitorear precios de propiedades de alojamiento y ayudar en la toma de decisiones de pricing.

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o contacta al desarrollador.
