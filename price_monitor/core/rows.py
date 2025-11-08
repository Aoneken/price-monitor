from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from price_monitor.core.io_csv import CSV_COLUMNS, INSERTED_AT_INDEX
from price_monitor.providers.airbnb import fetch_booking_price

# build_daymap import removed (not used here)

PRICE_PER_NIGHT_INDEX = CSV_COLUMNS.index("pricePerNight")
PRICE_BASIS_INDEX = CSV_COLUMNS.index("priceBasisNights")
TOTAL_PRICE_INDEX = CSV_COLUMNS.index("stayTotal")
NOTES_INDEX = CSV_COLUMNS.index("notes")


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


def check_min_stay_block(
    daymap: Dict[str, Any], start_day: date, nights: int
) -> Tuple[bool, Optional[str]]:
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


def build_rows(
    session,
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
    *,
    max_workers: int = 3,
    rich_progress=None,
    progress_task_id=None,
) -> List[List[str]]:
    rows_info: Dict[date, Dict[str, Any]] = {}
    dates = []
    cur = start_date
    while cur <= end_date:
        dates.append(cur)
        cur += timedelta(days=1)
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
                rows_info[current_day] = info
                continue
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

    # Prepare tasks
    tasks: List[Tuple[date, int]] = []
    covered: set[date] = set()
    for idx, current_day in enumerate(dates):
        info = rows_info[current_day]
        if info.get("cached_row") is not None:
            continue
        if current_day in covered:
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
        tasks.append((current_day, min_stay))
        for bd in block_dates:
            covered.add(bd)

    lock = threading.Lock()
    if tasks:
        with ThreadPoolExecutor(
            max_workers=max(1, min(8, int(max_workers)))
        ) as executor:
            future_map = {}
            for start_day, min_stay in tasks:
                future = executor.submit(
                    fetch_booking_price,
                    session,
                    listing_id,
                    start_day,
                    min_stay,
                    guests,
                    currency,
                    delay,
                    retries,
                )
                future_map[future] = (start_day, min_stay)
            for fut in as_completed(future_map):
                start_day, min_stay_local = future_map[fut]
                try:
                    per_night, total_price, extra_notes, error = fut.result()
                except (
                    Exception
                ) as exc:  # noqa: BLE001 intentionally broad: network/parse variability
                    per_night, total_price, extra_notes, error = (
                        None,
                        None,
                        [],
                        f"booking_exc:{type(exc).__name__}"[:200],
                    )
                with lock:
                    info = rows_info[start_day]
                    if error and error not in info["notes"]:
                        info["notes"].append(error)
                    else:
                        _apply_block_result(
                            rows_info,
                            dates,
                            start_day,
                            min_stay_local,
                            per_night,
                            total_price,
                            extra_notes,
                        )
                if rich_progress and progress_task_id is not None:
                    rich_progress.advance(progress_task_id, 1)

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


def _apply_block_result(
    rows_info: Dict[date, Dict[str, Any]],
    dates: List[date],
    start_day: date,
    min_stay_local: int,
    per_night: Optional[float],
    total_price: Optional[float],
    extra_notes: List[str],
) -> None:
    timestamp = datetime.now().isoformat()
    idx_local = dates.index(start_day)
    for offset, block_day in enumerate(dates[idx_local : idx_local + min_stay_local]):
        block_info = rows_info.get(block_day)
        if not block_info or block_info.get("day_obj") is None:
            continue
        if block_info.get("cached_row") is not None:
            continue
        if per_night is not None and block_info.get("price_per_night") is None:
            block_info["price_per_night"] = per_night
        if offset == 0 and total_price is not None:
            block_info["price_basis_nights"] = min_stay_local
            block_info["total_price"] = total_price
        else:
            carry_note = f"carried_from={start_day.isoformat()}"
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


def _parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None
