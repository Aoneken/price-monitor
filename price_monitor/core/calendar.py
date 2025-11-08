from __future__ import annotations

import time
import random
from datetime import date
from typing import Any, Dict
from urllib.parse import urlencode

import requests

from price_monitor.providers.airbnb import (
    GRAPHQL_BASE,
    CALENDAR_HASH,
    json_dumps_compact,
)


def month_count(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def fetch_calendar(
    session: requests.Session,
    listing_id: str,
    month: int,
    year: int,
    count: int,
    *,
    locale: str = "en",
    currency: str = "USD",
    retries: int = 3,
    delay: float = 0.5,
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
        "locale": locale,
        "currency": currency,
        "variables": json_dumps_compact(variables),
        "extensions": json_dumps_compact(
            {"persistedQuery": {"version": 1, "sha256Hash": CALENDAR_HASH}}
        ),
    }
    url = f"{GRAPHQL_BASE}/PdpAvailabilityCalendar/{CALENDAR_HASH}?{urlencode(params)}"
    last_exc: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            if attempt > 0:
                backoff = min(8.0, (2**attempt) * (delay or 0.5))
                time.sleep(backoff * (0.8 + 0.4 * random.random()))
            resp = session.get(url, timeout=30)
            if resp.status_code >= 500:
                last_exc = RuntimeError(f"calendar_http_{resp.status_code}")
            else:
                resp.raise_for_status()
                return resp.json()
        except requests.RequestException as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError("calendar_fetch_failed")


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
