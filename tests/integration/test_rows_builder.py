from datetime import date, timedelta

import pytest

from price_monitor.core.rows import build_rows
from price_monitor.core.io_csv import CSV_COLUMNS


@pytest.fixture()
def synthetic_daymap():
    # 3 days: first two available & bookable with minNights=2; third availableForCheckout True
    start = date(2025, 12, 1)
    days = []
    for i in range(3):
        d = start + timedelta(days=i)
        days.append({
            "calendarDate": d.isoformat(),
            "available": True,
            "availableForCheckin": True if i == 0 else False,
            "availableForCheckout": True if i == 2 else True,
            "bookable": True,
            "minNights": 2,
            "maxNights": 31,
        })
    # Map like build_daymap would produce
    return {day["calendarDate"]: day for day in days}


def test_build_rows_min_stay_block(monkeypatch, synthetic_daymap):
    # Monkeypatch fetch_booking_price used inside core.rows
    def fake_fetch_booking_price(session, listing_id, checkin, stay_nights, guests, currency, delay, retries):
        assert stay_nights == 2
        total = 200.0
        return total / stay_nights, total, ["base_total=160.00", "service_total=40.00"], None

    import price_monitor.core.rows as rows_mod
    monkeypatch.setattr(rows_mod, "fetch_booking_price", fake_fetch_booking_price)

    session = object()  # not used by fake
    listing_id = "TEST123"
    start_date = date(2025, 12, 1)
    end_date = date(2025, 12, 3)

    rows = build_rows(
        session,
        listing_id,
        start_date,
        end_date,
        guests=2,
        daymap=synthetic_daymap,
        currency="USD",
        locale="en",
        delay=0.0,
        retries=0,
        cache_hours=0,
        existing_rows={},
        max_workers=2,
        rich_progress=None,
        progress_task_id=None,
    )

    assert len(rows) == 3
    idx_price = CSV_COLUMNS.index("pricePerNight")
    idx_basis = CSV_COLUMNS.index("priceBasisNights")
    idx_total = CSV_COLUMNS.index("stayTotal")
    idx_notes = CSV_COLUMNS.index("notes")

    # Day 1 has prices and basis nights
    assert rows[0][idx_price] == "100.00"
    assert rows[0][idx_basis] == "2"
    assert rows[0][idx_total] == "200.00"

    # Day 2 carried prices per night (carried note present)
    assert rows[1][idx_price] == "100.00"
    assert "carried_from=" in rows[1][idx_notes]

    # Day 3 no price (outside block)
    assert rows[2][idx_price] == ""
