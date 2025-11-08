from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class DayRecord:
    date: date
    available: Optional[bool]
    available_for_checkin: Optional[bool]
    available_for_checkout: Optional[bool]
    bookable: Optional[bool]
    min_nights: Optional[int]
    max_nights: Optional[int]
    price_per_night: Optional[float]
    price_basis_nights: Optional[int]
    stay_total: Optional[float]
    currency: str
    inserted_at: Optional[datetime]
    notes: List[str]


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        from datetime import timedelta

        cur += timedelta(days=1)
