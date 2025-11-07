# Fase 5 – UI y API

## Objetivo
Proveer una interfaz desacoplada y/o API para operar y consultar el sistema.

## Alcance
- UI (Streamlit) enfocada en consulta/gestión.
- API (FastAPI) para orquestación y consumo de datos.
- Estados de tareas y progreso visible.

## Criterios de aceptación
- UI mínima para Establecimientos y estado de ingesta.
- Endpoints para disparar/postear tareas y leer resultados.

## Lecciones heredadas relevantes
- UI bloqueante → separar ejecución en background y consumir estado.
