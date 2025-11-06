# 🎯 Guía de Uso de VS Code Tasks - Price Monitor

## ¿Por qué usar Tasks de VS Code?

Las **Tasks** permiten ejecutar comandos en **segundo plano** sin bloquear tu terminal, con detección automática de problemas y gestión de procesos.

---

## 🚀 Cómo Iniciar el Servidor

### Método 1: Usando Command Palette (Recomendado)

1. **Abre Command Palette**: 
   - Windows/Linux: `Ctrl + Shift + P`
   - Mac: `Cmd + Shift + P`

2. **Escribe**: `Tasks: Run Task`

3. **Selecciona**: `Start Price Monitor`

4. **Listo**: El servidor se inicia en un terminal dedicado

### Método 2: Atajo de Teclado

1. **Presiona**: `Ctrl + Shift + B` (o `Cmd + Shift + B` en Mac)

2. **Selecciona**: `Start Price Monitor`

### Método 3: Desde el Menú

1. **Menu**: Terminal → Run Task...

2. **Selecciona**: `Start Price Monitor`

---

## 🛑 Cómo Detener el Servidor

### Opción 1: Usando Tasks

1. `Ctrl + Shift + P` → `Tasks: Run Task`
2. Selecciona: `Stop Price Monitor`

### Opción 2: Desde el Terminal

En el terminal donde corre Streamlit:
- Presiona `Ctrl + C`

### Opción 3: Script de Shell

```bash
./stop.sh
```

---

## 🔄 Reiniciar el Servidor

### Usando Task (Recomendado)

1. `Ctrl + Shift + P` → `Tasks: Run Task`
2. Selecciona: `Restart Price Monitor`

Esto detendrá y volverá a iniciar automáticamente.

---

## 📋 Tasks Disponibles

| Task | Descripción | Uso |
|------|-------------|-----|
| **Start Price Monitor** | Inicia servidor Streamlit | Build Task (Ctrl+Shift+B) |
| **Stop Price Monitor** | Detiene servidor | Manual |
| **Restart Price Monitor** | Detiene e inicia | Manual |
| **Run E2E Tests** | Ejecuta tests end-to-end | Manual |
| **Run Platform Tests** | Tests de scraping por plataforma | Manual |
| **View Streamlit Logs** | Muestra logs en tiempo real | Manual |

---

## 🐛 Debugging con VS Code

### Debug del Servidor Streamlit

1. **Abre**: Panel de Debug (Ctrl+Shift+D o Cmd+Shift+D)

2. **Selecciona**: `Debug Streamlit App`

3. **Presiona**: F5 o clic en ▶️

4. **Coloca breakpoints** en tu código

5. **Navega** en el navegador - VS Code pausará en breakpoints

### Debug de Tests

1. Panel de Debug → `Debug E2E Tests`
2. F5 para ejecutar con debugging

---

## ✨ Ventajas de usar Tasks

### ✅ **Ventajas sobre `nohup` y scripts**:

1. **Terminal Dedicado**: 
   - Cada task corre en su propio terminal
   - No bloquea otros terminales
   - Puedes ver logs en tiempo real

2. **Detección de Problemas**:
   - VS Code detecta cuando el servidor está listo
   - Marca errores automáticamente
   - Problem Matcher integrado

3. **Gestión de Procesos**:
   - VS Code trackea el proceso
   - Fácil detención con Ctrl+C
   - No quedan procesos huérfanos

4. **Una Sola Instancia**:
   - `instanceLimit: 1` previene múltiples servidores
   - Evita conflictos de puertos

5. **Integración Total**:
   - Funciona con debugging
   - Atajos de teclado
   - UI visual

---

## 📊 Verificar que Todo Funciona

### 1. Ver Procesos Activos

```bash
ps aux | grep streamlit
```

### 2. Ver Panel de Tasks

- **Menu**: Terminal → Show Running Tasks...
- Verás todas las tasks activas

### 3. Ver Logs en Tiempo Real

**Opción A**: Usar Task
1. `Ctrl + Shift + P` → `Tasks: Run Task`
2. `View Streamlit Logs`

**Opción B**: Comando directo
```bash
tail -f logs/streamlit.log
```

---

## 🎯 Workflow Recomendado

### Desarrollo Diario

```
1. Abrir VS Code
2. Ctrl + Shift + B → Start Price Monitor
3. Esperar mensaje "You can now view your Streamlit app"
4. Abrir navegador en http://localhost:8501
5. Desarrollar con hot reload automático
6. Al terminar: Ctrl + C en el terminal de Streamlit
```

### Testing

```
1. Ctrl + Shift + P → Tasks: Run Task
2. Run E2E Tests (para tests rápidos)
3. Run Platform Tests (para tests de scraping)
```

### Debugging

```
1. Colocar breakpoints en código
2. Ctrl + Shift + D → Debug Streamlit App
3. F5 para iniciar
4. Interactuar con la app en navegador
5. VS Code pausará en breakpoints
```

---

## 🔧 Configuración de Tasks

Archivo: `.vscode/tasks.json`

### Propiedades Clave

```json
{
    "isBackground": true,           // Corre en segundo plano
    "instanceLimit": 1,             // Solo 1 instancia a la vez
    "problemMatcher": {...},        // Detecta cuando está listo
    "presentation": {
        "panel": "dedicated"        // Terminal dedicado
    }
}
```

---

## 🆘 Troubleshooting

### Error: "Task 'Start Price Monitor' is already active"

**Causa**: Ya hay una instancia corriendo

**Solución**:
```
1. Ctrl + Shift + P → Tasks: Run Task
2. Stop Price Monitor
3. Luego: Start Price Monitor
```

### Error: "Address already in use (8501)"

**Causa**: Puerto ocupado por otro proceso

**Solución**:
```bash
# Ver qué usa el puerto
lsof -i :8501

# Matar proceso
pkill -f streamlit

# Reintentar
Ctrl + Shift + B → Start Price Monitor
```

### No veo logs en el terminal

**Solución**:
```
1. Menu: Terminal → Show Running Tasks
2. Clic en el terminal de "Start Price Monitor"
```

### Hot reload no funciona

**Solución**:
- Streamlit recarga automáticamente al guardar archivos .py
- Si no funciona: Restart Price Monitor

---

## 📝 Archivos de Configuración

```
.vscode/
├── tasks.json          → Definición de tasks
├── launch.json         → Configuración de debugging
└── settings.json       → Configuración de Python/Editor
```

### Personalizar Tasks

Edita `.vscode/tasks.json` para:
- Cambiar puerto: `--server.port=8502`
- Modo no-headless: `--server.headless=false`
- Agregar tus propias tasks

---

## ✅ Checklist de Inicio

- [ ] Configuración de VS Code cargada (.vscode/*)
- [ ] Python interpreter seleccionado
- [ ] Dependencias instaladas
- [ ] Task "Start Price Monitor" disponible en Command Palette
- [ ] Servidor inicia con Ctrl+Shift+B
- [ ] Navegador abre en http://localhost:8501
- [ ] Hot reload funciona al editar archivos

---

## 💡 Tips Pro

### 1. Atajos Personalizados

Edita `keybindings.json`:
```json
{
    "key": "ctrl+shift+s",
    "command": "workbench.action.tasks.runTask",
    "args": "Start Price Monitor"
}
```

### 2. Auto-Start en Workspace

Agrega a `.vscode/tasks.json`:
```json
{
    "runOptions": {
        "runOn": "folderOpen"
    }
}
```

### 3. Multi-Task Workflow

Crea una task compuesta:
```json
{
    "label": "Full Stack",
    "dependsOn": [
        "Start Price Monitor",
        "View Streamlit Logs"
    ]
}
```

---

## 🎉 Resultado Final

Con esta configuración, puedes:

✅ Iniciar servidor con 1 comando
✅ Múltiples terminales sin conflictos  
✅ Debugging integrado
✅ Hot reload automático
✅ Gestión profesional de procesos
✅ No más procesos huérfanos
✅ Logs organizados

**¡Desarrollo profesional en VS Code!** 🚀
