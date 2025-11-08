#!/usr/bin/env python3
"""Fetch real nightly prices and availability for Airbnb listings.

This script combines the availability calendar (GraphQL) with the public
explore search API to obtain per-night prices exactly as shown on airbnb.com.
It reads listing metadata from ``establecimientos.csv`` and generates one CSV
per establishment with nightly availability, minimum stay requirements and
real prices.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import re
from datetime import date, timedelta, datetime
from pathlib import Path
from typing import Dict, Any, Optional, Iterable, List, Tuple
from urllib.parse import urlencode

import requests


GRAPHQL_BASE = "https://www.airbnb.com.ar/api/v3"  # Base del endpoint GraphQL público.
CALENDAR_HASH = "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade"  # Hash persistido para el calendario PDP.
CHECKOUT_HASH = "106e2b2c6a2a8de04851b4b75e17cb653e6bfa3ea005deebd2f8520bb108163b"  # Hash para validar disponibilidad de checkout.
API_KEY = "d306zoyjsyarp7ifhu67rjxn52tv0t20"  # API key pública utilizada por Airbnb (la rotan periódicamente).

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "x-airbnb-api-key": API_KEY,
    "x-airbnb-graphql-platform": "web",
    "x-airbnb-graphql-platform-client": "minimalist-niobe",
    "x-csrf-without-token": "1",
}  # Encabezados comunes enviados en cada request HTTP a Airbnb.

CSV_COLUMNS = [
    "date",
    "available",
    "availableForCheckin",
    "availableForCheckout",
    "bookable",
    "minNights",
    "maxNights",
    "pricePerNight",
    "priceBasisNights",
    "stayTotal",
    "currency",
    "insertedAt",
    "notes",
]  # Orden de columnas en los CSV generados, para asegurar consistencia.

INSERTED_AT_INDEX = CSV_COLUMNS.index("insertedAt")  # Posición de la marca temporal.
PRICE_PER_NIGHT_INDEX = CSV_COLUMNS.index(
    "pricePerNight"
)  # Posición del precio por noche.
PRICE_BASIS_INDEX = CSV_COLUMNS.index(
    "priceBasisNights"
)  # Posición de la cantidad de noches base.
TOTAL_PRICE_INDEX = CSV_COLUMNS.index("stayTotal")  # Posición del total de la estadía.
NOTES_INDEX = CSV_COLUMNS.index("notes")  # Posición de las notas descriptivas.

BASE_LISTING_URL_TEMPLATE = "https://www.airbnb.com.ar/rooms/{listing_id}"  # URL base del alojamiento (se reemplaza {listing_id}).
DATE_INPUT_FORMAT = "%Y-%m-%d"  # Formato ISO 8601 utilizado en --start y --end.
DATE_FORMAT_DISPLAY = "YYYY-MM-DD"  # Representación amigable del formato de fecha.

DEFAULT_START_DATE = None  # Fecha inicial por defecto; usar None para exigir --start (formato YYYY-MM-DD).
DEFAULT_END_DATE = (
    None  # Fecha final por defecto; usar None para exigir --end (formato YYYY-MM-DD).
)
DEFAULT_GUESTS = 2  # Cantidad de huéspedes por defecto para cotizar.
DEFAULT_CURRENCY = "USD"  # Moneda para solicitar precios.
DEFAULT_LOCALE = "en"  # Locale base para los endpoints de explore.
DEFAULT_DELAY = 0.5  # Pausa entre requests consecutivos en segundos.
DEFAULT_RETRIES = 3  # Reintentos permitidos para cada request de precio real.
DEFAULT_CACHE_HOURS = (
    0.0  # Ventana (horas) para reutilizar datos existentes sin reconsultar.
)
DEFAULT_OUTPUT_DIR = Path(
    "output_real"
)  # Carpeta relativa donde se guardan los CSV generados.


def parse_establecimientos_csv(csv_path: Path) -> List[Dict[str, str]]:
    listings: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            airbnb_url = (row.get("Airbnb") or "").strip()
            if not airbnb_url:
                continue
            if "/rooms/" not in airbnb_url:
                continue
            listing_id = airbnb_url.split("/rooms/")[-1].split("?")[0].split("/")[0]
            listing_id = listing_id.strip()
            if not listing_id:
                continue
            listing_url = airbnb_url or BASE_LISTING_URL_TEMPLATE.format(
                listing_id=listing_id
            )
            listings.append(
                {
                    "listing_id": listing_id,
                    "Establecimiento": (row.get("Establecimiento") or "").strip(),
                    "Airbnb": listing_url,
                }
            )
    return listings


def print_listing_catalog(listings: List[Dict[str, str]]) -> None:
    """Mostrar catálogo numerado de establecimientos disponibles."""

    if not listings:
        print("No hay establecimientos disponibles.")
        return

    header = f"{'#':>3}  {'Establecimiento':40}  {'Listing ID':18}  URL"
    print(header)
    print("-" * len(header))
    for idx, item in enumerate(listings, start=1):
        name = item.get("Establecimiento", "").strip() or "(sin nombre)"
        listing_id = item.get("listing_id", "-")
        url = item.get("Airbnb", "-")
        print(f"{idx:>3}  {name[:40]:40}  {listing_id:18}  {url}")


def _select_token_indices(token: str, total: int) -> List[int]:
    if "-" in token:
        start_str, end_str = token.split("-", 1)
        if not (start_str.isdigit() and end_str.isdigit()):
            raise ValueError(f"Rango inválido: '{token}'")
        start = int(start_str)
        end = int(end_str)
        if start < 1 or end < start or end > total:
            raise ValueError(f"Rango fuera de límites: '{token}'")
        return list(range(start, end + 1))
    if token.isdigit():
        idx = int(token)
        if idx < 1 or idx > total:
            raise ValueError(f"Índice fuera de límites: '{token}'")
        return [idx]
    return []


def select_listings_by_tokens(
    listings: List[Dict[str, str]], selector: str
) -> List[Dict[str, str]]:
    """Seleccionar establecimientos mediante índices, IDs o nombres parciales."""

    tokens = [tok.strip() for tok in re.split(r"[\s,]+", selector) if tok.strip()]
    if not tokens:
        raise ValueError("No se especificaron selecciones válidas.")

    if any(tok.lower() in {"all", "todos"} for tok in tokens):
        return list(listings)

    selected: List[Dict[str, str]] = []
    seen_ids = set()

    for token in tokens:
        matched_items: List[Dict[str, str]] = []

        idx_list = _select_token_indices(token, len(listings))
        if idx_list:
            for idx in idx_list:
                item = listings[idx - 1]
                if item["listing_id"] not in seen_ids:
                    matched_items.append(item)
            selected.extend(matched_items)
            seen_ids.update(item["listing_id"] for item in matched_items)
            continue

        # Coincidencia por listing ID exacto
        for item in listings:
            if item["listing_id"] == token:
                matched_items = [item]
                break

        # Coincidencia por nombre (subcadena, insensible a mayúsculas)
        if not matched_items:
            normalized = token.lower()
            candidates = [
                item
                for item in listings
                if normalized in item.get("Establecimiento", "").lower()
            ]
            if len(candidates) == 1:
                matched_items = candidates
            elif len(candidates) > 1:
                raise ValueError(
                    f"Selección ambigua '{token}': coincide con varios establecimientos"
                )

        if not matched_items:
            raise ValueError(
                f"No se encontró un establecimiento que coincida con '{token}'"
            )

        for item in matched_items:
            listing_id = item["listing_id"]
            if listing_id not in seen_ids:
                selected.append(item)
                seen_ids.add(listing_id)

    if not selected:
        raise ValueError("La selección no produjo resultados.")

    return selected


def interactive_select(listings: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Selector interactivo desde la terminal."""

    print_listing_catalog(listings)
    print(
        "\nSelecciona establecimientos ingresando índices, IDs o fragmentos del nombre."
    )
    print("Separá múltiples entradas con comas. ENTER = todos. 'q' = cancelar.")
    response = input("Selección: ").strip()

    if not response:
        return list(listings)

    if response.lower() in {"q", "quit", "salir"}:
        return []

    return select_listings_by_tokens(listings, response)


def check_min_stay_block(
    daymap: Dict[str, Any], start_day: date, nights: int
) -> Tuple[bool, Optional[str]]:
    """Verifica si hay disponibilidad suficiente para cumplir la estadía mínima."""

    for offset in range(nights):
        current_day = start_day + timedelta(days=offset)
        current_obj = daymap.get(current_day.isoformat())
        if current_obj is None:
            return False, "minstay_missing_calendar"
        if not current_obj.get("available"):
            return False, "minstay_unavailable_segment"
        if offset == 0 and not current_obj.get("bookable"):
            return False, "minstay_not_bookable"

    checkout_day = start_day + timedelta(days=nights)
    checkout_obj = daymap.get(checkout_day.isoformat())
    if checkout_obj is not None and not checkout_obj.get("availableForCheckout"):
        return False, "minstay_checkout_blocked"

    return True, None


def _format_bool(value: Optional[bool]) -> str:
    if value is None:
        return ""
    return "True" if value else "False"


def _format_optional_number(value: Optional[Any]) -> str:
    if value is None:
        return ""
    return str(value)


def _format_price(value: Optional[float]) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def make_row(
    day: date,
    day_obj: Optional[Dict[str, Any]],
    price_per_night: Optional[float],
    price_basis_nights: Optional[int],
    total_price: Optional[float],
    currency: str,
    notes: Iterable[str],
    inserted_at: Optional[str],
) -> List[str]:
    unique_notes = list(dict.fromkeys(note for note in notes if note))
    day_info = day_obj or {}
    return [
        day.isoformat(),
        _format_bool(day_info.get("available")),
        _format_bool(day_info.get("availableForCheckin")),
        _format_bool(day_info.get("availableForCheckout")),
        _format_bool(day_info.get("bookable")),
        _format_optional_number(day_info.get("minNights")),
        _format_optional_number(day_info.get("maxNights")),
        _format_price(price_per_night),
        _format_optional_number(price_basis_nights),
        _format_price(total_price),
        currency,
        inserted_at or "",
        ";".join(unique_notes),
    ]


def _parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _extract_json_object(text: str, start: int) -> Optional[str]:
    length = len(text)
    index = start
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] != "{":
        return None

    brace_count = 0
    in_string = False
    escape = False
    for pos in range(index, length):
        ch = text[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[index : pos + 1]
    return None


def extract_price_breakdown_from_html(html: str) -> Optional[Dict[str, Any]]:
    marker = '"productPriceBreakdown":'
    idx = html.find(marker)
    if idx == -1:
        return None
    json_snippet = _extract_json_object(html, idx + len(marker))
    if not json_snippet:
        return None
    try:
        data = json.loads(json_snippet)
    except json.JSONDecodeError:
        return None
    return data.get("priceBreakdown") or data


def fetch_booking_price(
    session: requests.Session,
    listing_id: str,
    checkin: date,
    stay_nights: int,
    guests: int,
    currency: str,
    locale: str,
    delay: float,
    retries: int,
) -> Tuple[Optional[float], Optional[float], List[str], Optional[str]]:
    checkout = checkin + timedelta(days=stay_nights)
    url = f"https://www.airbnb.com.ar/book/stays/{listing_id}"
    params = {
        "checkin": checkin.isoformat(),
        "checkout": checkout.isoformat(),
        "numberOfGuests": guests,
        "numberOfAdults": guests,
        "numberOfChildren": 0,
        "numberOfInfants": 0,
        "numberOfPets": 0,
        "productId": listing_id,
        "guestCurrency": currency,
        "isWorkTrip": "false",
    }

    last_error: Optional[str] = None

    for attempt in range(max(1, retries)):
        try:
            response = session.get(url, params=params, timeout=60)
            if response.status_code >= 500:
                last_error = f"booking_http_{response.status_code}"
            else:
                response.raise_for_status()
                price_breakdown = extract_price_breakdown_from_html(response.text)
                if not price_breakdown:
                    last_error = "booking_price_not_found"
                else:
                    total_info = (price_breakdown.get("total") or {}).get("total") or {}
                    amount_micros = total_info.get("amountMicros")
                    if amount_micros is None:
                        last_error = "booking_total_missing"
                    else:
                        total_price = int(amount_micros) / 1_000_000
                        per_night = total_price / max(stay_nights, 1)
                        notes: List[str] = []
                        total_fmt = total_info.get("amountFormatted")
                        if total_fmt:
                            clean_total_fmt = total_fmt.replace("\xa0", " ").replace(
                                " ", ""
                            )
                            notes.append(f"total_fmt={clean_total_fmt}")

                        base_amount: Optional[float] = None
                        service_amount: Optional[float] = None

                        for item in price_breakdown.get("priceItems", []):
                            for nested in item.get("nestedPriceItems") or []:
                                label = (nested.get("localizedTitle") or "").lower()
                                total_nested = nested.get("total") or {}
                                nested_micros = total_nested.get("amountMicros")
                                if nested_micros is None:
                                    continue
                                value = int(nested_micros) / 1_000_000
                                label_clean = label.replace("\xa0", " ")
                                formatted = total_nested.get("amountFormatted") or ""
                                formatted_clean = formatted.replace(
                                    "\xa0", " "
                                ).replace(" ", "")
                                if (
                                    "servicio" in label_clean
                                    or "service" in label_clean
                                ):
                                    service_amount = value
                                    if formatted_clean:
                                        notes.append(f"service_fmt={formatted_clean}")
                                elif "noche" in label_clean or "night" in label_clean:
                                    base_amount = value
                                    if formatted_clean:
                                        notes.append(f"base_fmt={formatted_clean}")

                        if base_amount is not None:
                            notes.append(f"base_total={base_amount:.2f}")
                        if service_amount is not None:
                            notes.append(f"service_total={service_amount:.2f}")

                        return per_night, total_price, notes, None

        except requests.RequestException as exc:
            last_error = f"booking_error:{exc}"[:200]

        time.sleep(delay * (attempt + 1))

    return None, None, [], last_error or "booking_failed"


def month_count(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def fetch_calendar(
    session: requests.Session, listing_id: str, month: int, year: int, count: int
) -> Dict[str, Any]:
    variables = {
        "request": {
            "count": count,
            "listingId": listing_id,
            "month": month,
            "year": year,
        }
    }
    params = {
        "operationName": "PdpAvailabilityCalendar",
        "locale": "en",
        "currency": "USD",
        "variables": json_dumps_compact(variables),
        "extensions": json_dumps_compact(
            {"persistedQuery": {"version": 1, "sha256Hash": CALENDAR_HASH}}
        ),
    }
    url = f"{GRAPHQL_BASE}/PdpAvailabilityCalendar/{CALENDAR_HASH}?{urlencode(params)}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_daymap(calendar_data: Dict[str, Any]) -> Dict[str, Any]:
    months = (
        calendar_data.get("data", {})
        .get("merlin", {})
        .get("pdpAvailabilityCalendar", {})
        .get("calendarMonths", [])
    )
    daymap: Dict[str, Any] = {}
    for month in months:
        for day in month.get("days", []):
            key = day.get("calendarDate")
            if key:
                daymap[key] = day
    return daymap


def daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def sanitize_filename(name: str) -> str:
    safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe = "".join(ch for ch in safe if ch.isalnum() or ch in ("_", "-"))
    return safe or "listing"


def build_rows(
    session: requests.Session,
    listing_id: str,
    start_date: date,
    end_date: date,
    guests: int,
    daymap: Dict[str, Any],
    currency: str,
    locale: str,
    delay: float,
    retries: int,
    cache_hours: float,
    existing_rows: Dict[date, Dict[str, Any]],
) -> List[List[str]]:
    rows_info: Dict[date, Dict[str, Any]] = {}
    dates = list(daterange(start_date, end_date))
    today = date.today()
    now_dt = datetime.now()
    cache_cutoff = None
    if cache_hours and cache_hours > 0:
        cache_cutoff = now_dt - timedelta(hours=cache_hours)
    run_timestamp = now_dt.isoformat()

    for current_day in dates:
        day_key = current_day.isoformat()
        day_obj = daymap.get(day_key)
        existing_entry = existing_rows.get(current_day)
        existing_row: Optional[List[str]] = None
        existing_inserted_dt: Optional[datetime] = None
        existing_inserted_str: Optional[str] = None

        if existing_entry:
            existing_row = list(existing_entry.get("row", []))
            existing_inserted_dt = existing_entry.get("inserted_at")
            if existing_row and len(existing_row) > INSERTED_AT_INDEX:
                existing_inserted_str = existing_row[INSERTED_AT_INDEX] or None

        info: Dict[str, Any] = {
            "day": current_day,
            "day_obj": day_obj,
            "price_per_night": None,
            "price_basis_nights": None,
            "total_price": None,
            "notes": [],
            "available": None,
            "bookable": None,
            "can_checkin": None,
            "can_checkout": None,
            "min_stay": None,
            "cached_row": None,
            "inserted_at": existing_inserted_str,
        }

        is_pre_today = current_day < today
        is_cached = False
        if existing_row is not None:
            if is_pre_today:
                is_cached = True
            elif (
                cache_cutoff
                and existing_inserted_dt
                and existing_inserted_dt >= cache_cutoff
            ):
                is_cached = True

        if not day_obj:
            if is_cached and existing_row is not None:
                info["cached_row"] = existing_row
                info["price_per_night"] = _parse_optional_float(
                    existing_row[PRICE_PER_NIGHT_INDEX]
                )
                info["price_basis_nights"] = _parse_optional_int(
                    existing_row[PRICE_BASIS_INDEX]
                )
                info["total_price"] = _parse_optional_float(
                    existing_row[TOTAL_PRICE_INDEX]
                )
            else:
                info["notes"].append("no_calendar_data")
            rows_info[current_day] = info
            continue

        min_stay_raw = day_obj.get("minNights")
        min_stay = max(1, int(min_stay_raw if min_stay_raw else 1))
        available = bool(day_obj.get("available"))
        bookable = bool(day_obj.get("bookable"))
        can_checkin = bool(day_obj.get("availableForCheckin"))
        can_checkout = bool(day_obj.get("availableForCheckout"))

        info.update(
            {
                "min_stay": min_stay,
                "available": available,
                "bookable": bookable,
                "can_checkin": can_checkin,
                "can_checkout": can_checkout,
            }
        )

        if is_cached and existing_row is not None:
            info["cached_row"] = existing_row
            info["price_per_night"] = _parse_optional_float(
                existing_row[PRICE_PER_NIGHT_INDEX]
            )
            info["price_basis_nights"] = _parse_optional_int(
                existing_row[PRICE_BASIS_INDEX]
            )
            info["total_price"] = _parse_optional_float(existing_row[TOTAL_PRICE_INDEX])
        else:
            info["notes"].append(f"min_stay={min_stay}")
            if not available:
                info["notes"].append("unavailable")
            if available and not bookable:
                info["notes"].append("not_bookable")
            if available and bookable and not can_checkin:
                info["notes"].append("no_checkin")
            if available and not can_checkout:
                info["notes"].append("no_checkout")

        rows_info[current_day] = info

    for idx, current_day in enumerate(dates):
        info = rows_info[current_day]
        if info.get("cached_row") is not None:
            continue
        day_obj = info.get("day_obj")
        if not day_obj:
            continue
        if not (
            info.get("available") and info.get("bookable") and info.get("can_checkin")
        ):
            continue

        min_stay = info["min_stay"]
        remaining = len(dates) - idx
        if remaining < min_stay:
            if (
                info.get("price_per_night") is None
                and "insufficient_range" not in info["notes"]
            ):
                info["notes"].append("insufficient_range")
            continue

        block_ok, reason = check_min_stay_block(daymap, current_day, min_stay)
        if not block_ok:
            if reason and reason not in info["notes"]:
                info["notes"].append(reason)
            continue

        block_dates = dates[idx : idx + min_stay]
        if all(
            (
                rows_info[day].get("cached_row") is not None
                or rows_info[day]["price_per_night"] is not None
            )
            for day in block_dates
        ):
            continue

        per_night, total_price, extra_notes, error = fetch_booking_price(
            session,
            listing_id,
            current_day,
            min_stay,
            guests,
            currency,
            locale,
            delay,
            retries,
        )

        if error:
            if error not in info["notes"]:
                info["notes"].append(error)
            continue

        timestamp = datetime.now().isoformat()
        for offset, block_day in enumerate(block_dates):
            block_info = rows_info.get(block_day)
            if not block_info or block_info.get("day_obj") is None:
                continue
            if block_info.get("cached_row") is not None:
                continue

            if block_info["price_per_night"] is None:
                block_info["price_per_night"] = per_night
            if offset == 0:
                block_info["price_basis_nights"] = min_stay
                block_info["total_price"] = total_price
            else:
                carry_note = f"carried_from={current_day.isoformat()}"
                if carry_note not in block_info["notes"]:
                    block_info["notes"].append(carry_note)

            if block_info["day_obj"] and not block_info["day_obj"].get(
                "availableForCheckin"
            ):
                if "no_checkin" not in block_info["notes"]:
                    block_info["notes"].append("no_checkin")
            if block_info["day_obj"] and not block_info["day_obj"].get(
                "availableForCheckout"
            ):
                if "no_checkout" not in block_info["notes"]:
                    block_info["notes"].append("no_checkout")

            for note in extra_notes:
                if note not in block_info["notes"]:
                    block_info["notes"].append(note)

            block_info["inserted_at"] = block_info.get("inserted_at") or timestamp

    final_rows: List[List[str]] = []
    for current_day in dates:
        info = rows_info[current_day]
        if info.get("cached_row") is not None:
            final_rows.append(info["cached_row"])
            continue
        inserted_at = info.get("inserted_at") or run_timestamp
        final_rows.append(
            make_row(
                current_day,
                info.get("day_obj"),
                info.get("price_per_night"),
                info.get("price_basis_nights"),
                info.get("total_price"),
                currency,
                info.get("notes", []),
                inserted_at,
            )
        )

    return final_rows


def load_existing_rows(output_path: Path) -> Dict[date, Dict[str, Any]]:
    if not output_path.exists():
        return {}

    existing: Dict[date, Dict[str, Any]] = {}
    with output_path.open("r", encoding="utf-8", newline="") as handle:

        def data_lines():
            for raw_line in handle:
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                yield raw_line

        reader = csv.reader(data_lines())
        header = next(reader, None)
        if not header:
            return {}

        header_map = {name: idx for idx, name in enumerate(header)}

        for row in reader:
            if not row:
                continue
            normalized = ["" for _ in CSV_COLUMNS]
            for name, idx in header_map.items():
                if name not in CSV_COLUMNS:
                    continue
                if idx < len(row):
                    normalized[CSV_COLUMNS.index(name)] = row[idx]

            try:
                row_date = date.fromisoformat(normalized[0])
            except ValueError:
                continue

            inserted_dt: Optional[datetime] = None
            inserted_str = normalized[INSERTED_AT_INDEX]
            if inserted_str:
                try:
                    inserted_dt = datetime.fromisoformat(inserted_str)
                except ValueError:
                    inserted_dt = None

            existing[row_date] = {"row": normalized, "inserted_at": inserted_dt}

    return existing


def write_csv(
    output_path: Path,
    listing_name: str,
    listing_id: str,
    listing_url: str,
    start_date: date,
    end_date: date,
    guests: int,
    rows: List[List[str]],
    cache_hours: float,
    existing_rows: Dict[date, Dict[str, Any]],
):
    today = date.today()
    frozen_rows: Dict[date, List[str]] = {
        day: info.get("row", []) for day, info in existing_rows.items() if day < today
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"# Listing: {listing_name}\n")
        handle.write(f"# Listing ID: {listing_id}\n")
        handle.write(f"# Listing URL: {listing_url}\n")
        handle.write(f"# Period: {start_date.isoformat()} to {end_date.isoformat()}\n")
        handle.write(f"# Guests: {guests}\n")
        handle.write(f"# Generated: {datetime.now().isoformat()}\n")
        handle.write(f"# Cache Hours: {cache_hours}\n")
        handle.write("#\n")
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            try:
                row_day = date.fromisoformat(row[0])
            except ValueError:
                writer.writerow(row)
                continue

            if row_day < today and row_day in frozen_rows:
                writer.writerow(frozen_rows[row_day])
            else:
                writer.writerow(row)


def json_dumps_compact(data: Any) -> str:
    import json

    return json.dumps(data, separators=(",", ":"))


def resolve_csv_path(explicit: Optional[Path]) -> Path:
    if explicit:
        return explicit
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent.parent.parent / "establecimientos" / "establecimientos.csv",
        script_dir.parent.parent / "establecimientos" / "establecimientos.csv",
        script_dir.parent / "establecimientos" / "establecimientos.csv",
        Path.cwd() / "establecimientos" / "establecimientos.csv",
        Path.cwd()
        / "Foco_01"
        / "Temp-25-26"
        / "establecimientos"
        / "establecimientos.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No se encontró establecimientos.csv; especifica --csv")


def filter_listings(
    listings: List[Dict[str, str]], target_ids: Optional[List[str]]
) -> List[Dict[str, str]]:
    if not target_ids:
        return listings
    target = {tid.strip() for tid in target_ids}
    return [item for item in listings if item["listing_id"] in target]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download real nightly prices + availability for Airbnb listings"
    )
    start_required = DEFAULT_START_DATE is None
    end_required = DEFAULT_END_DATE is None
    start_help = f"Fecha de inicio del período ({DATE_FORMAT_DISPLAY})." + (
        " Obligatoria si DEFAULT_START_DATE es None."
        if start_required
        else f" Valor por defecto: {DEFAULT_START_DATE}."
    )
    end_help = f"Fecha de fin del período ({DATE_FORMAT_DISPLAY})." + (
        " Obligatoria si DEFAULT_END_DATE es None."
        if end_required
        else f" Valor por defecto: {DEFAULT_END_DATE}."
    )

    parser.add_argument(
        "--start",
        default=DEFAULT_START_DATE,
        required=start_required,
        help=start_help,
    )
    parser.add_argument(
        "--end",
        default=DEFAULT_END_DATE,
        required=end_required,
        help=end_help,
    )
    parser.add_argument(
        "--guests",
        type=int,
        default=DEFAULT_GUESTS,
        help=(f"Cantidad de huéspedes para la cotización (default: {DEFAULT_GUESTS})"),
    )
    parser.add_argument("--csv", type=Path, help="Ruta a establecimientos.csv")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directorio de salida (default: ./{DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--listing-id",
        action="append",
        help="Procesar solo estos listing IDs (puede repetirse)",
    )
    parser.add_argument(
        "--select",
        help=(
            "Selecciona establecimientos por índices, IDs o nombres. "
            "Ejemplo: '1,3-5,Patagonia'"
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Abre un selector interactivo antes de comenzar el scraping",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Muestra el catálogo de establecimientos y termina",
    )
    parser.add_argument(
        "--currency",
        default=DEFAULT_CURRENCY,
        help=f"Código de moneda (default: {DEFAULT_CURRENCY})",
    )
    parser.add_argument(
        "--locale",
        default=DEFAULT_LOCALE,
        help=f"Locale para el API de explore (default: {DEFAULT_LOCALE})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=(
            "Delay en segundos entre requests a explore_tabs (default:"
            f" {DEFAULT_DELAY})"
        ),
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Reintentos por request de precio (default: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--cache-hours",
        type=float,
        default=DEFAULT_CACHE_HOURS,
        help=(
            "Horas de caché para reutilizar registros existentes y evitar nuevas"
            f" consultas (default: {DEFAULT_CACHE_HOURS})"
        ),
    )

    args = parser.parse_args(argv)

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    if end_date < start_date:
        parser.error("--end debe ser >= --start")

    csv_path = resolve_csv_path(args.csv)
    all_listings = parse_establecimientos_csv(csv_path)
    if not all_listings:
        print("No se encontraron listings con URL de Airbnb en el CSV", file=sys.stderr)
        return 1

    if args.list:
        print_listing_catalog(all_listings)
        return 0

    listings = filter_listings(all_listings, args.listing_id)
    if not listings:
        print("Los listing IDs especificados no están en el CSV", file=sys.stderr)
        return 1

    if args.select:
        try:
            listings = select_listings_by_tokens(listings, args.select)
        except ValueError as exc:
            parser.error(str(exc))

    if args.interactive:
        listings = interactive_select(listings)
        if not listings:
            print("Operación cancelada por el usuario.", file=sys.stderr)
            return 0

    output_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else (Path.cwd() / args.output_dir)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(COMMON_HEADERS)
    session.headers["Accept-Language"] = f"{args.locale},en;q=0.8,es;q=0.7"

    total_months = month_count(start_date, end_date)

    for listing in listings:
        listing_id = listing["listing_id"]
        listing_name = listing["Establecimiento"] or f"Listing {listing_id}"
        listing_url = listing["Airbnb"]

        print(f"Procesando {listing_name} ({listing_id})", file=sys.stderr)
        try:
            calendar_data = fetch_calendar(
                session, listing_id, start_date.month, start_date.year, total_months
            )
        except requests.RequestException as exc:
            print(f"  Error calendario: {exc}", file=sys.stderr)
            continue

        daymap = build_daymap(calendar_data)
        output_path = (
            output_dir
            / f"{sanitize_filename(listing_name)}_{start_date}_{end_date}.csv"
        )
        existing_rows = load_existing_rows(output_path)
        rows = build_rows(
            session,
            listing_id,
            start_date,
            end_date,
            args.guests,
            daymap,
            args.currency,
            args.locale,
            args.delay,
            args.retries,
            args.cache_hours,
            existing_rows,
        )
        write_csv(
            output_path,
            listing_name,
            listing_id,
            listing_url,
            start_date,
            end_date,
            args.guests,
            rows,
            args.cache_hours,
            existing_rows,
        )
        print(f"  CSV listo: {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
