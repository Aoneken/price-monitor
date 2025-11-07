#!/usr/bin/env python3
import os
import re
import json
import sqlite3
from datetime import date, timedelta
from contextlib import closing

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit("Playwright no instalado en este entorno. Activa .venv e instala playwright.")

DB_CANDIDATES = [
    os.path.join("database", "price_monitor.db"),
    os.path.join("precio_monitor.db"),
]

AMENITY_PATTERNS = {
    "wifi": re.compile(r"\b(wi\s*-?fi|wifi|internet)\b", re.I),
    "breakfast": re.compile(r"\b(desayuno|breakfast)\b", re.I),
}

CLEANING_PATTERNS = [
    re.compile(r"cleaning fee", re.I),
    re.compile(r"resort fee", re.I),
    re.compile(r"service fee", re.I),
    re.compile(r"tarifa de limpieza", re.I),
]
PRICE_REGEX = re.compile(r"([€$]|USD|EUR)\s?([0-9][0-9\.,\s]*)")


def find_db_path():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No se encontró base de datos en database/price_monitor.db ni precio_monitor.db")


def get_expedia_urls(limit=3):
    db_path = find_db_path()
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT url FROM Plataformas_URL
                WHERE plataforma = 'Expedia' AND (esta_activa = 1 OR esta_activa = TRUE OR esta_activa IS NULL)
                LIMIT ?
                """,
                (limit,),
            )
        except sqlite3.OperationalError:
            raise SystemExit("La tabla Plataformas_URL no existe en la BD seleccionada.")
        return [r["url"] for r in cur.fetchall()]


def url_variants(base, check_in, check_out):
    # Expedia suele aceptar chkin/chkout y también checkIn/checkOut
    common = "adults=2&children=0&currency=USD"
    v1 = f"{base}?chkin={check_in}&chkout={check_out}&{common}"
    v2 = f"{base}?checkIn={check_in}&checkOut={check_out}&{common}"
    return [v1, v2]


def extract_text_matches(text):
    wifi = bool(AMENITY_PATTERNS["wifi"].search(text))
    breakfast = bool(AMENITY_PATTERNS["breakfast"].search(text))
    cleaning_aparte = any(p.search(text) for p in CLEANING_PATTERNS)
    price_match = PRICE_REGEX.search(text)
    price_text = price_match.group(0) if price_match else None
    return wifi, breakfast, cleaning_aparte, price_text


def run_exploration(urls, nights=2, headless=True):
    check_in = (date.today() + timedelta(days=60)).isoformat()
    check_out = (date.today() + timedelta(days=60 + nights)).isoformat()
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="es-ES")
        page = context.new_page()
        captured = []

        def on_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                url = resp.url
                if "application/json" in ct and ("expedia" in url or "travel" in url):
                    if any(k in url.lower() for k in ["rate", "price", "availability", "room"]):
                        # limitar tamaño
                        text = resp.text()
                        if len(text) < 200000:
                            captured.append({"url": url, "body": text})
            except Exception:
                pass

        page.on("response", on_response)

        for base in urls:
            outcome = {
                "base_url": base,
                "check_in": check_in,
                "check_out": check_out,
                "tried": [],
                "found": False,
                "wifi": None,
                "breakfast": None,
                "cleaning_aparte": None,
                "price_text": None,
                "notes": [],
            }

            for u in url_variants(base, check_in, check_out):
                outcome["tried"].append(u)
                try:
                    page.goto(u, wait_until="networkidle", timeout=90000)
                    # Interacciones suaves para forzar carga de tarifas
                    # Intentar aceptar cookies si aparece
                    for consent in ["Aceptar", "Aceptar todo", "Accept all", "Estoy de acuerdo"]:
                        try:
                            btnc = page.get_by_text(consent, exact=False)
                            if btnc and btnc.is_visible():
                                btnc.click(timeout=1500)
                                page.wait_for_timeout(500)
                                break
                        except Exception:
                            pass

                    for txt in [
                        "Ver disponibilidad",
                        "Seleccionar fechas",
                        "See availability",
                        "Ver ofertas",
                        "Elegir habitación",
                        "Ver habitaciones",
                        "Seleccionar habitación",
                        "Choose room",
                    ]:
                        try:
                            btn = page.get_by_text(txt, exact=False)
                            if btn and btn.is_visible():
                                btn.click(timeout=2000)
                                page.wait_for_load_state("networkidle")
                                page.wait_for_timeout(1500)
                                break
                        except Exception:
                            pass
                    # Scroll para hidratar lazy content
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                    content = page.content()
                    wifi, breakfast, cleaning_aparte, price_text = extract_text_matches(content)

                    # Intentar extraer precio de JSON capturado si DOM no dio
                    if not price_text and captured:
                        import json as _json
                        for item in captured[-10:]:
                            try:
                                data = _json.loads(item["body"]) if item["body"].strip().startswith("{") else None
                                if not data:
                                    continue
                                # Heurística: buscar campos con nightly/perNight/amount
                                def walk(obj):
                                    if isinstance(obj, dict):
                                        for k, v in obj.items():
                                            kl = str(k).lower()
                                            if kl in ("nightly", "pernight", "amount", "price") and isinstance(v, (int, float, str)):
                                                yield v
                                            yield from walk(v)
                                    elif isinstance(obj, list):
                                        for v in obj:
                                            yield from walk(v)
                                for val in walk(data):
                                    s = str(val)
                                    m = re.search(r"([0-9]{2,4}[\.,]?[0-9]{0,2})", s)
                                    if m:
                                        price_text = m.group(1)
                                        break
                                if price_text:
                                    break
                            except Exception:
                                continue

                    if any([wifi, breakfast, cleaning_aparte, price_text]):
                        outcome.update({
                            "found": True,
                            "wifi": "Sí" if wifi else "No",
                            "breakfast": "Sí" if breakfast else "No",
                            "cleaning_aparte": "Sí" if cleaning_aparte else "No",
                            "price_text": price_text,
                        })
                        break
                    else:
                        outcome["notes"].append("Sin matches claros en DOM inicial")
                except Exception as e:
                    outcome["notes"].append(f"Error navegando: {e}")
            results.append(outcome)

        context.close()
        browser.close()
    return results


def main():
    urls = get_expedia_urls(limit=3)
    headless = os.getenv("HEADLESS", "true").lower() == "true"
    results = run_exploration(urls, nights=2, headless=headless)

    out_path = os.path.join("docs_v3", "RESULTADOS_EXPLORACION_EXPEDIA.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Resultados de Exploración Expedia (Automático)\n\n")
        for r in results:
            f.write(f"## Listing\n")
            f.write(f"- Base URL: {r['base_url']}\n")
            f.write(f"- Check-in: {r['check_in']}\n")
            f.write(f"- Check-out: {r['check_out']}\n")
            f.write(f"- Variantes probadas: {len(r['tried'])}\n")
            f.write(f"- Encontrado: {r['found']}\n")
            f.write(f"- WiFi incluido: {r['wifi']}\n")
            f.write(f"- Desayuno incluido: {r['breakfast']}\n")
            f.write(f"- Limpieza aparte: {r['cleaning_aparte']}\n")
            f.write(f"- Precio (snippet): {r['price_text']}\n")
            if r["notes"]:
                f.write(f"- Notas: {' | '.join(r['notes'])}\n")
            f.write("\n---\n\n")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nResultados escritos en {out_path}")


if __name__ == "__main__":
    main()
