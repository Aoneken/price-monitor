from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from price_monitor.core.calendar import month_count, fetch_calendar, build_daymap
from price_monitor.core.selection import parse_establecimientos_csv, select_listings_by_tokens
from price_monitor.core.io_csv import load_existing_rows, write_csv
from price_monitor.providers.airbnb import COMMON_HEADERS, fetch_booking_price

# Reuse logic from original script (simplified build process) ------------------


def build_rows(
    session: requests.Session,
    listing_id: str,
    start_date: date,
    end_date: date,
    guests: int,
    daymap,
    currency: str,
    locale: str,
    delay: float,
    retries: int,
):
    # Minimal subset: only availability + direct booking attempt per first available block of min stay.
    from datetime import datetime, timedelta

    dates = []
    cur = start_date
    while cur <= end_date:
        dates.append(cur)
        cur += timedelta(days=1)

    rows = []
    for d in dates:
        iso = d.isoformat()
        day_obj = daymap.get(iso)
        notes = []
        price_per_night = ""
        price_basis_nights = ""
        stay_total = ""
        min_nights = ""
        max_nights = ""
        currency_code = ""
        if day_obj:
            available = day_obj.get("available")
            bookable = day_obj.get("bookable")
            min_nights = day_obj.get("minNights")
            max_nights = day_obj.get("maxNights")
            if available and bookable and day_obj.get("availableForCheckin"):
                # Try fetch a price block of min_nights
                mn = max(1, int(min_nights or 1))
                per, total, extra, err = fetch_booking_price(
                    session,
                    listing_id,
                    d,
                    mn,
                    guests,
                    currency,
                    locale,
                    delay,
                    retries,
                )
                if err:
                    notes.append(err)
                else:
                    price_per_night = f"{per:.2f}"
                    price_basis_nights = str(mn)
                    stay_total = f"{total:.2f}"
                    currency_code = currency
                    notes.extend(extra)
            row = [
                iso,
                str(day_obj.get("available")),
                str(day_obj.get("availableForCheckin")),
                str(day_obj.get("availableForCheckout")),
                str(day_obj.get("bookable")),
                str(min_nights or ""),
                str(max_nights or ""),
                price_per_night,
                price_basis_nights,
                stay_total,
                currency_code,
                datetime.now().isoformat(),
                ";".join(notes),
            ]
        else:
            row = [iso, "", "", "", "", "", "", "", "", "", "", "", "no_calendar_data"]
        rows.append(row)
    return rows


# CLI -------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Price Monitor CLI (Airbnb MVP)")
    p.add_argument("scrape-airbnb", nargs="?", help="Modo scrape Airbnb (subcomando implícito)")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--guests", type=int, default=2)
    p.add_argument("--csv", type=Path)
    p.add_argument("--select", help="Selector de establecimientos (índices, ID, fragmento nombre)")
    p.add_argument("--listing-id", action="append")
    p.add_argument("--currency", default="USD")
    p.add_argument("--locale", default="en")
    p.add_argument("--delay", type=float, default=0.4)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--output-dir", type=Path, default=Path("output"))

    args = p.parse_args(argv)

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    if end_date < start_date:
        p.error("--end >= --start")

    # Resolve CSV
    csv_path = args.csv
    if not csv_path:
        candidates = [
            Path("tests/Foco_01/Temp-25-26/establecimientos/establecimientos.csv"),
            Path("Foco_01/Temp-25-26/establecimientos/establecimientos.csv"),
        ]
        for c in candidates:
            if c.exists():
                csv_path = c
                break
    if not csv_path or not csv_path.exists():
        p.error("No se encontró establecimientos.csv")

    all_listings = parse_establecimientos_csv(csv_path)
    if not all_listings:
        print("CSV sin listings Airbnb", file=sys.stderr)
        return 1

    listings = all_listings
    if args.listing_id:
        ids = set(x.strip() for x in args.listing_id)
        listings = [l for l in listings if l["listing_id"] in ids]
        if not listings:
            print("IDs no presentes en CSV", file=sys.stderr)
            return 1

    if args.select:
        listings = select_listings_by_tokens(listings, args.select)

    session = requests.Session()
    session.headers.update(COMMON_HEADERS)

    total_months = month_count(start_date, end_date)

    console = Console(stderr=True)
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Scrape[/]"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("listings", total=len(listings))
        for listing in listings:
            listing_id = listing["listing_id"]
            name = listing["Establecimiento"] or listing_id
            console.rule(f"[cyan]{name}[/] ({listing_id})")
            try:
                cal = fetch_calendar(
                    session,
                    listing_id,
                    start_date.month,
                    start_date.year,
                    total_months,
                    locale=args.locale,
                    currency=args.currency,
                    retries=args.retries,
                    delay=args.delay,
                )
            except Exception as exc:  # noqa
                console.print(f"[red]Error calendario:[/] {exc}")
                progress.advance(task)
                continue
            daymap = build_daymap(cal)
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
            )
            out_dir = args.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            from price_monitor.core.io_csv import CSV_COLUMNS

            output_path = out_dir / f"{name.replace(' ', '_')}_{start_date}_{end_date}.csv"
            # Minimal write without caching reuse for this MVP CLI wrapper
            from datetime import datetime
            from csv import writer

            with output_path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(f"# Listing: {name}\n")
                handle.write(f"# Listing ID: {listing_id}\n")
                handle.write(f"# Listing URL: https://www.airbnb.com.ar/rooms/{listing_id}\n")
                handle.write(f"# Period: {start_date} to {end_date}\n")
                handle.write(f"# Guests: {args.guests}\n")
                handle.write(f"# Generated: {datetime.now().isoformat()}\n")
                handle.write("#\n")
                w = writer(handle)
                w.writerow(CSV_COLUMNS)
                w.writerows(rows)
            console.print(f"[green]OK[/] {output_path}")
            progress.advance(task)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
