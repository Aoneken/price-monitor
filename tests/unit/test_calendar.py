from datetime import date
from price_monitor.core.calendar import month_count, build_daymap


def test_month_count_simple():
    assert month_count(date(2025, 11, 8), date(2025, 11, 30)) == 1
    assert month_count(date(2025, 11, 8), date(2026, 1, 5)) == 3


def test_build_daymap_empty():
    assert (
        build_daymap(
            {"data": {"merlin": {"pdpAvailabilityCalendar": {"calendarMonths": []}}}}
        )
        == {}
    )
