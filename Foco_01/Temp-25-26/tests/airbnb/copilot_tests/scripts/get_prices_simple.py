#!/usr/bin/env python3
"""Generate per-night pricing + availability CSV for an Airbnb listing.

SIMPLIFIED VERSION: Due to Airbnb API authentication requirements, this script:
1. Fetches availability from PdpAvailabilityCalendar (works with API key)
2. For pricing, uses one of these approaches:
   a) Reads manual pricing data from a JSON file (--pricing-file)
   b) Uses a fixed per-night rate (--fixed-rate)
   c) Scrapes prices from saved HTML (future enhancement)

Usage examples:

  # Using availability only (no pricing):
  python3 scripts/get_prices_simple.py \\
      --listing-id 928978094650118177 \\
      --start 2025-12-10 \\
      --end 2025-12-20 \\
      --guests 2 \\
      --out tmp/availability.csv

  # With fixed nightly rate:
  python3 scripts/get_prices_simple.py \\
      --listing-id 928978094650118177 \\
      --start 2025-12-10 \\
      --end 2025-12-20 \\
      --guests 2 \\
      --fixed-rate 200 \\
      --out tmp/prices.csv

  # With manual pricing data:
  python3 scripts/get_prices_simple.py \\
      --listing-id 928978094650118177 \\
      --start 2025-12-10 \\
      --end 2025-12-20 \\
      --guests 2 \\
      --pricing-file tmp/manual_prices.json \\
      --out tmp/prices.csv

Manual pricing file format (JSON):
{
  "2025-12-10": 200.00,
  "2025-12-11": 200.00,
  "2025-12-12": 220.00
}

Output CSV format:
  # Metadata header with listing info, period, guests
  date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,notes
"""

from __future__ import annotations

import argparse
import csv
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


def load_pricing_file(path: Path) -> Dict[str, float]:
    """Load manual pricing data from JSON file.

    Expected format: {"2025-12-10": 200.00, "2025-12-11": 200.00, ...}
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def find_listing_in_csv(listing_id: str, csv_path: Path) -> Optional[Dict[str, str]]:
    """Find listing info in establecimientos.csv by Airbnb listing ID.

    Returns dict with keys: 'Establecimiento', 'Airbnb', 'Booking', 'Expedia'
    or None if not found.
    """
    if not csv_path.exists():
        return None

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            airbnb_url = row.get("Airbnb", "").strip()
            # Extract listing ID from URL like https://www.airbnb.com.ar/rooms/928978094650118177
            if airbnb_url and listing_id in airbnb_url:
                return row

    return None


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
    pricing: Dict[str, float],
    currency: str,
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
            "date,available,availableForCheckin,availableForCheckout,bookable,minNights,maxNights,pricePerNight,currency,notes\n"
        )

        # Data rows
        for d in daterange(start, end):
            day_str = d.isoformat()
            day_obj = daymap.get(day_str)
            price = pricing.get(day_str)

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
                    "no_calendar_data",
                ]
            else:
                price_str = f"{price:.2f}" if price is not None else ""
                notes = ""
                if price is None and day_obj.get("bookable"):
                    notes = "price_unavailable"

                row = [
                    day_str,
                    str(day_obj.get("available")),
                    str(day_obj.get("availableForCheckin")),
                    str(day_obj.get("availableForCheckout")),
                    str(day_obj.get("bookable")),
                    str(day_obj.get("minNights")),
                    str(day_obj.get("maxNights")),
                    price_str,
                    currency if price is not None else "",
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

    # Pricing options (mutually exclusive)
    pricing_group = p.add_mutually_exclusive_group()
    pricing_group.add_argument(
        "--pricing-file",
        type=Path,
        help='Path to JSON file with manual pricing data (format: {"2025-12-10": 200.00, ...})',
    )
    pricing_group.add_argument(
        "--fixed-rate",
        type=float,
        help="Fixed nightly rate to apply to all bookable dates",
    )

    p.add_argument(
        "--currency",
        default="USD",
        help="Currency code for pricing (default: USD)",
    )

    p.add_argument(
        "--establecimientos-csv",
        type=Path,
        help="Path to establecimientos.csv (auto-detected if not provided)",
    )

    args = p.parse_args(argv)

    listing_id = args.listing_id
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    guests = args.guests
    out_path = Path(args.out)
    currency = args.currency

    # Try to find listing info in establecimientos.csv
    listing_name = args.listing_name
    listing_url = args.listing_url

    if not listing_name or not listing_url:
        # Auto-detect establecimientos.csv path
        csv_path = args.establecimientos_csv
        if not csv_path:
            # Try common locations relative to script
            script_dir = Path(__file__).parent
            candidates = [
                script_dir / "../../../../../establecimientos/establecimientos.csv",
                script_dir / "../../../../../../establecimientos/establecimientos.csv",
                Path.cwd() / "establecimientos/establecimientos.csv",
                Path.cwd() / "Foco_01/Temp-25-26/establecimientos/establecimientos.csv",
            ]
            for candidate in candidates:
                if candidate.exists():
                    csv_path = candidate
                    break

        if csv_path and csv_path.exists():
            listing_info = find_listing_in_csv(listing_id, csv_path)
            if listing_info:
                if not listing_name:
                    listing_name = listing_info.get("Establecimiento", "").strip()
                    print(f"Found listing name in CSV: {listing_name}", file=sys.stderr)
                if not listing_url:
                    listing_url = listing_info.get("Airbnb", "").strip()

    # Fallbacks
    if not listing_name:
        listing_name = f"Listing {listing_id}"
    if not listing_url:
        listing_url = f"https://www.airbnb.com.ar/rooms/{listing_id}"

    listing_url = listing_url or f"https://www.airbnb.com.ar/rooms/{listing_id}"
    currency = args.currency

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

    # Load or generate pricing
    pricing: Dict[str, float] = {}

    if args.pricing_file:
        print(f"Loading pricing from {args.pricing_file}...", file=sys.stderr)
        pricing = load_pricing_file(args.pricing_file)
    elif args.fixed_rate:
        print(f"Using fixed rate: ${args.fixed_rate} per night", file=sys.stderr)
        # Apply fixed rate to all bookable dates
        for d in daterange(start_date, end_date):
            day_str = d.isoformat()
            day_obj = daymap.get(day_str)
            if day_obj and day_obj.get("bookable"):
                pricing[day_str] = args.fixed_rate
    else:
        print(
            "No pricing data provided. Output will contain availability only.",
            file=sys.stderr,
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
        pricing,
        currency,
        out_path,
    )

    print(f"Done. Output written to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
