# human_info — capturas y notas manuales

Propósito

Almacenar capturas manuales y notas de soporte (HARs, exportaciones de
red, ejemplos de selectores) que sirven como referencia para reproducir
peticiones y depurar extractores.

Estructura recomendada

- `elements/`: ejemplos de selectores y fragmentos útiles por listing.
- `network/messages*`: exportaciones textuales de tráfico de red.
- `har/`: HARs originales exportadas desde el navegador.

Uso con los scripts del repositorio

1. Localizar la HAR o el archivo `messages` que contiene la petición
   `PdpAvailabilityCalendar` para el listing y mes de interés.
2. Reproducir la petición (offline) con `scripts/replay_endpoint.py`:

   `python3 scripts/replay_endpoint.py --url "<FULL_URL>" --out tmp/calendar.json --no-compression`

3. Convertir el JSON resultante a CSV con `scripts/get_availability.py`.

Buenas prácticas

- Mantener los archivos originales sin editar; crear copias para transformaciones.
- Registrar metadatos (URL completa, fechas, parámetros usados) al capturar.
- Nombrar archivos con contexto: `HAR_<dominio>_<listing>_<YYYY-MM-DD>.har`.

Limitaciones

- Algunos endpoints requieren contexto de sesión (cookies/headers) y no se
  reproducen correctamente fuera del navegador. En esos casos, capture XHRs
  localmente (Playwright) y guarde el HAR/JSON en esta carpeta.
- El material puede contener datos sensibles; trátelo con precaución.

Archivo generado automáticamente: `human_info/README.md`
