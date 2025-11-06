# 🎬 Guía de Usuario - Price Monitor v2.0

## 🚀 Inicio Rápido

### Paso 1: Inicia la Aplicación

```bash
cd /workspaces/price-monitor
streamlit run app.py
```

**URL**: `http://localhost:8501`

---

## 🧭 Navegación Principal

### Tab 1: 📊 Dashboard

**¿Qué verás?**
- **4 Métricas principales** con gradientes visuales:
  - Total de registros almacenados
  - Número de propiedades monitoreadas
  - Precio promedio general
  - Última actualización

- **Gráfico de evolución**: Líneas de tiempo mostrando cómo varían los precios por propiedad
- **Comparación por plataforma**: Gráfico de barras con promedio de cada plataforma
- **Tabla resumen**: Estadísticas por propiedad

**¿Cuándo usar?**
- Al abrir la app (primera vista)
- Para ver el estado general del sistema
- Para identificar tendencias rápidamente

**Mensaje especial**: Si no hay datos, verás un mensaje de bienvenida guiándote a agregar competidores y hacer scraping.

---

### Tab 2: 🔍 Nuevo Scraping

**¿Qué verás?**

#### Selector de Propiedad
- Dropdown con todas las propiedades configuradas
- Expandible con información de URLs

#### Configuración de Fechas (Columna Izquierda)
- **Fecha de inicio**: DatePicker
- **Días a scrapear**: Slider (1-30 días)
- **Resumen**: Muestra rango completo calculado

#### Configuración de Reserva (Columna Derecha)
- **Número de huéspedes**: Input numérico (1-16)
- **Número de noches**: Input numérico (1-30)
- **Resumen**: Muestra configuración en texto

#### Selector de Plataformas
- ☑️ Airbnb
- ☑️ Booking

#### Botón de Scraping
- Grande, azul, centrado
- **"🚀 Iniciar Scraping"**

**¿Qué pasa al hacer clic?**

1. **Validación**: Verifica que todo esté correcto
2. **Barra de progreso**: Muestra avance en tiempo real
3. **Estado textual**: Indica qué plataforma está scrapeando
4. **Mensajes de éxito**: Confirma cuántos registros se obtuvieron
5. **Preview de resultados**: Tabla expandible con datos obtenidos

**Flujo completo**:
```
Seleccionar → Configurar → Elegir Plataformas → Scrapear → Ver Resultados
```

---

### Tab 3: 📈 Datos Históricos

**¿Qué verás?**

#### Selector de Propiedad
- Dropdown para elegir qué propiedad analizar

#### Estadísticas por Plataforma
- **Tarjetas visuales** para cada plataforma (Airbnb/Booking)
- Métricas mostradas:
  - Precio Mínimo
  - Precio Promedio
  - Precio Máximo
  - Total de Registros

#### Gráfico de Evolución
- Líneas de tiempo por plataforma
- Interactivo (zoom, pan, hover)
- Muestra precio vs fecha de check-in

#### Dos Gráficos Adicionales (Lado a Lado)

**Izquierda: Diferencia de Precios**
- Gráfico de barras
- Verde = Airbnb más barato
- Rojo = Airbnb más caro
- Muestra diferencia (Airbnb - Booking)

**Derecha: Distribución de Precios**
- Histogramas
- Box plots
- Por plataforma

#### Tabla de Datos Detallados

**Filtros disponibles**:
- Por plataforma (multiselect)
- Solo con precio (checkbox)

**Características**:
- Ordenable por columna
- Scroll vertical
- Formato limpio

#### Exportación

**Dos opciones**:
1. **📥 Exportar a Excel**: Crea archivo en carpeta `data/`
2. **📥 Descargar CSV**: Descarga directa al navegador

**Nombres de archivo**: Incluyen timestamp automático

---

### Tab 4: 🏢 Gestión de Competidores

**Dos Sub-tabs**:

#### 📋 Competidores Existentes

**¿Qué verás?**
- **Tarjetas por cada competidor**:
  - Nombre destacado
  - URLs de Airbnb y Booking (con iconos)
  - Botón "🗑️ Eliminar"

**¿Cómo eliminar?**
1. Clic en "Eliminar" → Aparece advertencia
2. Clic nuevamente → Se elimina
3. Confirmación visual

**Efecto hover**: Las tarjetas se elevan al pasar el mouse

#### ➕ Agregar Nuevo

**Formulario**:
```
🏨 Nombre de la Propiedad: [____________]
                          (Texto único)

🔗 URLs de Plataformas:
   🏠 URL de Airbnb:  [____________________________]
   🏨 URL de Booking: [____________________________]

   [💾 Guardar Competidor]
```

**Validaciones**:
- ❌ Nombre obligatorio
- ❌ Al menos una URL requerida
- ❌ No permitir duplicados

**Al guardar**:
- ✅ Mensaje de éxito
- 🎈 Animación de globos
- 🔄 Refresca la lista

---

## 🔧 Sidebar (Siempre Visible)

### Sección 1: Información Rápida
- **Competidores Registrados**: Número total
- **Registros Totales**: Cantidad de datos
- **Última actualización**: Fecha y hora

### Sección 2: Enlaces
- 📖 Documentación
- 🏗️ Arquitectura
- 📝 Ejemplos

### Sección 3: Footer
- Versión de la app

---

## 💡 Tips y Trucos

### 1. Primer Uso
```
1. Ir a "Gestión de Competidores"
2. Agregar una propiedad
3. Ir a "Nuevo Scraping"
4. Configurar y scrapear
5. Ver resultados en "Dashboard" y "Datos Históricos"
```

### 2. Configuración Óptima de Scraping
- **Días a scrapear**: 
  - 7 días → Semana completa
  - 14 días → Dos semanas
  - 30 días → Mes completo

- **Noches**:
  - 1 noche → Precios de una sola noche
  - 2-3 noches → Fin de semana
  - 7 noches → Semana completa

### 3. Interpretación de Gráficos

**Evolución de Precios**:
- Líneas ascendentes = Precios subiendo
- Líneas descendentes = Precios bajando
- Líneas paralelas = Precios estables

**Diferencia de Precios**:
- Barras verdes grandes = Airbnb mucho más barato
- Barras rojas grandes = Airbnb mucho más caro
- Barras pequeñas = Precios similares

**Distribución**:
- Box plot ancho = Mayor variación de precios
- Box plot estrecho = Precios consistentes
- Outliers = Precios excepcionales

### 4. Mejores Prácticas

#### Frecuencia de Scraping
```
Recomendado:
- Semanal: Para seguimiento general
- Diario: Para fechas específicas importantes
- Mensual: Para análisis de tendencias
```

#### Cantidad de Datos
```
Mínimo para análisis útil:
- 2 semanas de datos
- Múltiples scrapes
- Ambas plataformas
```

#### Exportación
```
Usa Excel si:
- Necesitas análisis offline
- Vas a compartir con otros
- Quieres pivot tables

Usa CSV si:
- Necesitas importar a otra herramienta
- Archivo más ligero
- Procesamiento con pandas
```

---

## 🎨 Significado de Colores

### Métricas
- **Morado**: Información general
- **Rosado**: Propiedades
- **Azul claro**: Precios
- **Naranja/Rosa**: Fechas

### Alertas
- **Verde**: Éxito ✅
- **Azul**: Información 💡
- **Amarillo**: Advertencia ⚠️
- **Rojo**: Error ❌

### Gráficos
- **Airbnb**: #FF5A5F (Rojo corporativo)
- **Booking**: #003580 (Azul corporativo)

---

## 🐛 Solución de Problemas

### "No hay competidores registrados"
**Solución**: Ve a "Gestión de Competidores" → "Agregar Nuevo"

### "No hay datos históricos"
**Solución**: Realiza un scraping en "Nuevo Scraping"

### El scraping falla
**Posibles causas**:
1. URL incorrecta → Verifica en la plataforma
2. Fechas inválidas → Usa fechas futuras
3. Internet lento → Espera y reintenta

### Los gráficos no se muestran
**Solución**: 
1. Verifica que haya datos
2. Selecciona una propiedad válida
3. Refresca la página

### Error al exportar
**Solución**:
1. Verifica permisos de carpeta `data/`
2. Cierra archivos Excel abiertos
3. Libera espacio en disco

---

## ⌨️ Atajos y Shortcuts

### Navegación
- **Tab**: Moverse entre campos
- **Enter**: Enviar formulario
- **Esc**: Cerrar expandibles

### Gráficos (Plotly)
- **Click + Arrastrar**: Zoom en área
- **Doble Click**: Reset zoom
- **Hover**: Ver detalles
- **Botón Cámara**: Descargar como PNG
- **Botón Zoom**: Herramientas de zoom

---

## 📊 Ejemplos de Uso

### Caso 1: Monitoreo Semanal
```
Objetivo: Ver tendencia de precios de mi competidor

1. Dashboard → Ver estado general
2. Nuevo Scraping → 
   - Seleccionar competidor
   - 7 días
   - 2 huéspedes, 1 noche
   - Ambas plataformas
3. Datos Históricos → Ver evolución
4. Repetir semanalmente
```

### Caso 2: Análisis de Temporada Alta
```
Objetivo: Comparar precios en temporada alta

1. Nuevo Scraping →
   - Fechas de temporada alta
   - 30 días
   - Configuración típica
2. Datos Históricos →
   - Ver distribución
   - Identificar picos
3. Exportar a Excel → Análisis offline
```

### Caso 3: Comparación Múltiple
```
Objetivo: Ver todos mis competidores

1. Agregar múltiples competidores
2. Scrapear cada uno
3. Dashboard → Comparar en tabla resumen
4. Identificar el más competitivo
```

---

## 🎓 Glosario

**Check-in**: Fecha de entrada a la propiedad
**Check-out**: Fecha de salida
**Scraping**: Extracción automática de datos
**Precio USD**: Precio en dólares americanos
**Huéspedes**: Número de personas
**Noches**: Duración de la estadía
**Plataforma**: Airbnb o Booking
**Registro**: Un dato de precio específico
**Propiedad**: Competidor a monitorear

---

## 📞 Recursos Adicionales

### Documentación
- `README.md`: Introducción general
- `QUICKSTART.md`: Guía rápida
- `ARCHITECTURE.md`: Detalles técnicos
- `UX_IMPROVEMENTS.md`: Mejoras de interfaz
- `REFACTORING_SUMMARY.md`: Resumen de cambios

### Código
- `app.py`: Interfaz principal
- `src/`: Módulos de scraping y análisis
- `config/`: Configuración de competidores

### Datos
- `data/price_history.csv`: Histórico de precios
- `data/*.xlsx`: Exportaciones Excel

---

**¡Disfruta tu nueva herramienta de monitoreo de precios! 💰✨**

**Si tienes dudas, revisa la documentación o explora la interfaz - está diseñada para ser intuitiva. 🎯**
