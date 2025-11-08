from __future__ import annotations

import json
import random
import time
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

GRAPHQL_BASE = "https://www.airbnb.com.ar/api/v3"
CALENDAR_HASH = "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade"
API_KEY = "d306zoyjsyarp7ifhu67rjxn52tv0t20"

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
}


def json_dumps_compact(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"))


def extract_price_breakdown_from_html(html: str) -> Optional[Dict[str, Any]]:
    marker = '"productPriceBreakdown":'
    idx = html.find(marker)
    if idx == -1:
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
            if attempt > 0:
                backoff = min(8.0, (2**attempt) * (delay or 0.5))
                time.sleep(backoff * (0.8 + 0.4 * random.random()))
            per_req_sleep = max(0.0, (delay or 0.0)) * (0.5 + random.random())
            if per_req_sleep:
                time.sleep(per_req_sleep)
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
                            clean_total_fmt = total_fmt.replace("\xa0", " ").replace(" ", "")
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
                                formatted_clean = formatted.replace("\xa0", " ").replace(" ", "")
                                if ("servicio" in label_clean or "service" in label_clean):
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
        time.sleep(min(2.0, (delay or 0.2) * (attempt + 1)))
    return None, None, [], last_error or "booking_failed"
