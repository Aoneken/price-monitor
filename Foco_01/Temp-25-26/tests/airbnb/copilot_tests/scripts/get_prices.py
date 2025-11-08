#!/usr/bin/env python3
"""Generate per-night pricing + availability CSV for an Airbnb listing.

This script fetches both availability (via PdpAvailabilityCalendar) and pricing
(via stayCheckout) for a given listing across a date range, then produces a CSV
with date, availability flags, and nightly price derived from stay totals.

Usage:
  python3 scripts/get_prices.py \\
      --listing-id 928978094650118177 \\
      --start 2025-12-10 \\
      --end 2025-12-20 \\
      --guests 2 \\
      --out tmp/prices_output.csv

Inputs:
  - listing-id: Airbnb listing identifier
  - start/end: Date range (YYYY-MM-DD)
  - guests: Number of guests (adults)
  - out: Output CSV path

Output CSV format:
  # Metadata header:
  # Listing: <name>
  # Listing URL: <url>
  # Period: <start> to <end>
  # Guests: <count>
  # Generated: <timestamp>

  date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,stayTotal,notes

Strategy:
  1. Query PdpAvailabilityCalendar for the full range to get availability flags
  2. For each bookable window (consecutive bookable nights >= minNights),
     query stayCheckout to get the stay total price
  3. Divide stay total by number of nights to get per-night estimate
  4. Emit CSV with availability + pricing per day
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta, datetime
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlencode

import requests


# GraphQL endpoints
GRAPHQL_BASE = "https://www.airbnb.com.ar/api/v3"
CALENDAR_HASH = "8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade"
CHECKOUT_HASH = "106e2b2c6a2a8de04851b4b75e17cb653e6bfa3ea005deebd2f8520bb108163b"

# Request headers (from HAR capture)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "x-airbnb-api-key": "d306zoyjsyarp7ifhu67rjxn52tv0t20",
    "x-airbnb-graphql-platform": "web",
    "x-airbnb-graphql-platform-client": "minimalist-niobe",
    "x-csrf-without-token": "1",
}


def fetch_calendar(
    listing_id: str, month: int, year: int, count: int = 12
) -> Dict[str, Any]:
    """Fetch PdpAvailabilityCalendar for a listing starting from month/year."""
    variables = {
        "request": {
            "count": count,
            "listingId": listing_id,
            "month": month,
            "year": year,
        }
    }
    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": CALENDAR_HASH,
        }
    }
    params = {
        "operationName": "PdpAvailabilityCalendar",
        "locale": "es-AR",
        "currency": "USD",
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps(extensions, separators=(",", ":")),
    }
    url = f"{GRAPHQL_BASE}/PdpAvailabilityCalendar/{CALENDAR_HASH}?{urlencode(params)}"

    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_checkout(
    listing_id: str,
    checkin: date,
    checkout: date,
    adults: int,
) -> Dict[str, Any]:
    """Fetch stayCheckout for a specific date range."""
    # Build POST body matching the observed request structure
    # The actual GraphQL query is persisted server-side
    variables = {
        "request": {
            "params": {
                "checkin": checkin.isoformat(),
                "checkout": checkout.isoformat(),
                "numberOfGuests": adults,
                "numberOfAdults": adults,
                "numberOfChildren": 0,
                "numberOfInfants": 0,
                "numberOfPets": 0,
                "productId": listing_id,
                "guestCurrency": "USD",
                "isWorkTrip": False,
            }
        }
    }
    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": CHECKOUT_HASH,
        }
    }
    params = {
        "operationName": "stayCheckout",
        "locale": "es-AR",
        "currency": "USD",
    }
    url = f"{GRAPHQL_BASE}/stayCheckout/{CHECKOUT_HASH}?{urlencode(params)}"

    # POST with JSON body
    body = {
        "operationName": "stayCheckout",
        "variables": variables,
        "extensions": extensions,
    }

    resp = requests.post(url, json=body, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_daymap(calendar_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse calendar months into a date->day mapping."""
    months = calendar_data["data"]["merlin"]["pdpAvailabilityCalendar"][
        "calendarMonths"
    ]
    daymap: Dict[str, Any] = {}
    for m in months:
        for d in m.get("days", []):
            if d.get("calendarDate"):
                daymap[d.get("calendarDate")] = d
    return daymap


def extract_stay_price(checkout_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract total stay price from stayCheckout response.

    Returns dict with keys: total_micros, currency, formatted, breakdown
    or None if not available.
    """
    try:
        sections = checkout_data["data"]["presentation"]["stayCheckout"]["sections"]
        quick_pay = sections["temporaryQuickPayData"]["bootstrapPayments"]
        price_breakdown = quick_pay["productPriceBreakdown"]["priceBreakdown"]

        total_item = price_breakdown["total"]
        total_currency = total_item["total"]

        # Extract nested items for breakdown
        price_items = price_breakdown.get("priceItems", [])
        breakdown = []
        for item in price_items:
            title = item.get("localizedTitle", "")
            amount = item["total"]["amountFormatted"]
            breakdown.append({"title": title, "amount": amount})

        return {
            "total_micros": int(total_currency["amountMicros"]),
            "currency": total_currency["currency"],
            "formatted": total_currency["amountFormatted"],
            "breakdown": breakdown,
        }
    except (KeyError, TypeError) as e:
        print(f"Warning: Could not extract price: {e}", file=sys.stderr)
        return None


def calculate_nightly_price(
    listing_id: str,
    start: date,
    end: date,
    adults: int,
    daymap: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Calculate per-night prices by querying stayCheckout for bookable windows.

    Returns dict: date_str -> {"price_per_night": float, "currency": str, "notes": str}
    """
    result = {}

    # Find bookable windows
    current = start
    while current <= end:
        day_str = current.isoformat()
        day_obj = daymap.get(day_str)

        if not day_obj or not day_obj.get("bookable"):
            # Not bookable, skip
            result[day_str] = {
                "price_per_night": None,
                "currency": None,
                "notes": "not_bookable",
            }
            current += timedelta(days=1)
            continue

        # Find consecutive bookable nights starting here
        if not day_obj.get("availableForCheckin"):
            result[day_str] = {
                "price_per_night": None,
                "currency": None,
                "notes": "no_checkin",
            }
            current += timedelta(days=1)
            continue

        min_nights = day_obj.get("minNights", 1)
        # Try to book min_nights from this checkin
        checkout_date = current + timedelta(days=min_nights)

        # Verify checkout date is valid
        if checkout_date > end:
            result[day_str] = {
                "price_per_night": None,
                "currency": None,
                "notes": "beyond_range",
            }
            current += timedelta(days=1)
            continue

        checkout_day = daymap.get(checkout_date.isoformat())
        if not checkout_day or not checkout_day.get("availableForCheckout"):
            result[day_str] = {
                "price_per_night": None,
                "currency": None,
                "notes": "no_valid_checkout",
            }
            current += timedelta(days=1)
            continue

        # Query stayCheckout
        print(
            f"Querying price for {current.isoformat()} -> {checkout_date.isoformat()} ({min_nights} nights)...",
            file=sys.stderr,
        )
        try:
            checkout_data = fetch_checkout(listing_id, current, checkout_date, adults)
            price_info = extract_stay_price(checkout_data)

            if price_info:
                total = (
                    price_info["total_micros"] / 1_000_000
                )  # Convert micros to currency units
                per_night = total / min_nights
                currency = price_info["currency"]

                # Assign same per-night price to all nights in this stay
                for i in range(min_nights):
                    d = current + timedelta(days=i)
                    if d > end:
                        break
                    result[d.isoformat()] = {
                        "price_per_night": per_night,
                        "currency": currency,
                        "stay_total": total,
                        "notes": f"stay_{min_nights}n",
                    }

                current += timedelta(days=min_nights)
            else:
                result[day_str] = {
                    "price_per_night": None,
                    "currency": None,
                    "notes": "price_unavailable",
                }
                current += timedelta(days=1)

        except Exception as e:
            print(f"Error querying checkout: {e}", file=sys.stderr)
            result[day_str] = {
                "price_per_night": None,
                "currency": None,
                "notes": f"error: {e}",
            }
            current += timedelta(days=1)

    return result


def daterange(start: date, end: date):
    """Generate dates from start to end inclusive."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def write_csv(
    listing_id: str,
    listing_url: str,
    listing_name: str,
    start: date,
    end: date,
    guests: int,
    daymap: Dict[str, Any],
    prices: Dict[str, Dict[str, Any]],
    out: Path,
) -> None:
    """Write CSV with metadata header and per-day rows."""
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        # Metadata header
        f.write(f"# Listing: {listing_name}\n")
        f.write(f"# Listing ID: {listing_id}\n")
        f.write(f"# Listing URL: {listing_url}\n")
        f.write(f"# Period: {start.isoformat()} to {end.isoformat()}\n")
        f.write(f"# Guests: {guests}\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write("#\n")

        # CSV header
        f.write(
            "date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,stayTotal,notes\n"
        )

        # Data rows
        for d in daterange(start, end):
            day_str = d.isoformat()
            day_obj = daymap.get(day_str)
            price_obj = prices.get(day_str, {})

            if not day_obj:
                row = [
                    day_str,
                    "missing",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "no_calendar_data",
                ]
            else:
                price_per_night = price_obj.get("price_per_night")
                currency = price_obj.get("currency", "")
                stay_total = price_obj.get("stay_total", "")
                notes = price_obj.get("notes", "")

                row = [
                    day_str,
                    str(day_obj.get("available")),
                    str(day_obj.get("availableForCheckin")),
                    str(day_obj.get("availableForCheckout")),
                    str(day_obj.get("bookable")),
                    str(day_obj.get("minNights")),
                    str(day_obj.get("maxNights")),
                    f"{price_per_night:.2f}" if price_per_night else "",
                    currency,
                    f"{stay_total:.2f}" if stay_total else "",
                    notes,
                ]

            line = ",".join(f'"{x}"' for x in row)
            f.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Generate per-night pricing + availability CSV for an Airbnb listing."
    )
    p.add_argument("--listing-id", required=True, help="Airbnb listing ID")
    p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p.add_argument(
        "--guests", type=int, default=2, help="Number of guests (default: 2)"
    )
    p.add_argument("--out", required=True, help="Output CSV path")
    p.add_argument(
        "--listing-name", default="", help="Listing name for header (optional)"
    )
    p.add_argument(
        "--listing-url", default="", help="Listing URL for header (optional)"
    )

    args = p.parse_args(argv)

    listing_id = args.listing_id
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    guests = args.guests
    out_path = Path(args.out)
    listing_name = args.listing_name or f"Listing {listing_id}"
    listing_url = args.listing_url or f"https://www.airbnb.com.ar/rooms/{listing_id}"

    print(
        f"Fetching availability calendar for listing {listing_id}...", file=sys.stderr
    )

    # Fetch calendar starting from start_date month
    calendar_data = fetch_calendar(
        listing_id,
        start_date.month,
        start_date.year,
        count=12,  # Fetch enough months
    )

    daymap = build_daymap(calendar_data)

    print(
        f"Calculating prices for date range {start_date} to {end_date}...",
        file=sys.stderr,
    )

    prices = calculate_nightly_price(
        listing_id,
        start_date,
        end_date,
        guests,
        daymap,
    )

    print(f"Writing CSV to {out_path}...", file=sys.stderr)

    write_csv(
        listing_id,
        listing_url,
        listing_name,
        start_date,
        end_date,
        guests,
        daymap,
        prices,
        out_path,
    )

    print(f"Done. Output written to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
