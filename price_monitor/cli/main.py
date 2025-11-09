from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from price_monitor.core.calendar import build_daymap, fetch_calendar, month_count
from price_monitor.core.io_csv import CSV_COLUMNS, load_existing_rows, write_csv
from price_monitor.core.rows import build_rows
from price_monitor.core.selection import (
    parse_establecimientos_csv,
    select_listings_by_tokens,
)
from price_monitor.providers.airbnb import COMMON_HEADERS

# CLI -------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Price Monitor CLI (Airbnb MVP)")
    p.add_argument(
        "scrape-airbnb", nargs="?", help="Modo scrape Airbnb (subcomando implícito)"
    )
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--guests", type=int, default=2)
    p.add_argument("--csv", type=Path)
    p.add_argument(
        "--select", help="Selector de establecimientos (índices, ID, fragmento nombre)"
    )
    p.add_argument("--listing-id", action="append")
    p.add_argument("--currency", default="USD")
    p.add_argument("--locale", default="en")
    p.add_argument("--delay", type=float, default=0.4)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument(
        "--cache-hours",
        type=float,
        default=6.0,
        help="Horas para reutilizar filas recientes",
    )
    p.add_argument(
        "--max-workers", type=int, default=4, help="Máximo de hilos para precios"
    )
    p.add_argument(
        "--no-rich",
        action="store_true",
        help="Desactivar barra Rich (modo texto simple)",
    )
    p.add_argument("--output-dir", type=Path, default=Path("output"))
    p.add_argument(
        "--freeze-before",
        type=str,
        default=None,
        help="Congelar filas anteriores a esta fecha (YYYY-MM-DD)",
    )
    p.add_argument("--json", action="store_true", help="Emitir JSON junto al CSV")

    args = p.parse_args(argv)

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    freeze_before = None
    if args.freeze_before:
        try:
            freeze_before = date.fromisoformat(args.freeze_before)
        except ValueError:
            p.error("--freeze-before debe ser YYYY-MM-DD")
    if end_date < start_date:
        p.error("--end >= --start")

    # Resolve CSV
    csv_path = args.csv
    if not csv_path:
        candidates = [
            Path("data/establecimientos.csv"),
            Path("tests/fixtures/establecimientos.csv"),
            Path("establecimientos.csv"),
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
        listings = [lst for lst in listings if lst["listing_id"] in ids]
        if not listings:
            print("IDs no presentes en CSV", file=sys.stderr)
            return 1

    if args.select:
        listings = select_listings_by_tokens(listings, args.select)

    session = requests.Session()
    session.headers.update(COMMON_HEADERS)

    total_months = month_count(start_date, end_date)

    console = Console(stderr=True)

    def estimate_booking_tasks(daymap: Dict[str, Any]) -> int:
        # Replica ligera de la lógica de bloques para contar futuras llamadas a precios.
        dates: List[date] = []
        cur = start_date
        while cur <= end_date:
            dates.append(cur)
            cur += timedelta(days=1)
        tasks_local = 0
        covered: set[date] = set()
        for idx, current_day in enumerate(dates):
            if current_day in covered:
                continue
            day_obj = daymap.get(current_day.isoformat())
            if not day_obj:
                continue
            available = bool(day_obj.get("available"))
            bookable = bool(day_obj.get("bookable"))
            can_checkin = bool(day_obj.get("availableForCheckin"))
            if not (available and bookable and can_checkin):
                continue
            min_nights_raw = day_obj.get("minNights")
            min_stay = max(1, int(min_nights_raw if min_nights_raw else 1))
            remaining = len(dates) - idx
            if remaining < min_stay:
                continue
            # Marcar los días cubiertos por el bloque
            for block_day in dates[idx : idx + min_stay]:
                covered.add(block_day)
            tasks_local += 1
        return tasks_local

    if args.no_rich:
        console.print(f"Listados: {len(listings)}")
        for i, listing in enumerate(listings, 1):
            listing_id = listing["listing_id"]
            name = listing["Establecimiento"] or listing_id
            console.print(f"[{i}/{len(listings)}] {name} ({listing_id})")
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
            except requests.RequestException as exc:
                console.print(f"[red]Error calendario:[/] {exc}")
                continue
            daymap = build_daymap(cal)
            out_dir = args.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = (
                out_dir / f"{name.replace(' ', '_')}_{start_date}_{end_date}.csv"
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
                max_workers=args.max_workers,
            )
            write_csv(
                output_path,
                name,
                listing_id,
                f"https://www.airbnb.com.ar/rooms/{listing_id}",
                start_date,
                end_date,
                args.guests,
                rows,
                args.cache_hours,
                existing_rows,
                freeze_before=freeze_before,
            )
            if args.json:
                json_path = output_path.with_suffix(".json")
                row_dicts = [
                    {col: row[idx] if idx < len(row) else "" for idx, col in enumerate(CSV_COLUMNS)}  # type: ignore[name-defined]
                    for row in rows
                ]
                with json_path.open("w", encoding="utf-8") as jh:
                    json.dump(row_dicts, jh, ensure_ascii=False, indent=2)
            console.print(f"[green]OK[/] {output_path}")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scrape[/]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            listings_task = progress.add_task("listings", total=len(listings))
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
                except requests.RequestException as exc:
                    console.print(f"[red]Error calendario:[/] {exc}")
                    progress.advance(listings_task)
                    continue
                daymap = build_daymap(cal)
                tasks_estimate = estimate_booking_tasks(daymap)
                booking_task = None
                if tasks_estimate:
                    booking_task = progress.add_task(
                        f"booking:{name}", total=tasks_estimate
                    )
                out_dir = args.output_dir
                out_dir.mkdir(parents=True, exist_ok=True)
                output_path = (
                    out_dir / f"{name.replace(' ', '_')}_{start_date}_{end_date}.csv"
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
                    max_workers=args.max_workers,
                    rich_progress=progress if booking_task is not None else None,
                    progress_task_id=booking_task,
                )
                write_csv(
                    output_path,
                    name,
                    listing_id,
                    f"https://www.airbnb.com.ar/rooms/{listing_id}",
                    start_date,
                    end_date,
                    args.guests,
                    rows,
                    args.cache_hours,
                    existing_rows,
                    freeze_before=freeze_before,
                )
                if args.json:
                    json_path = output_path.with_suffix(".json")
                    row_dicts = [
                        {col: row[idx] if idx < len(row) else "" for idx, col in enumerate(CSV_COLUMNS)}  # type: ignore[name-defined]
                        for row in rows
                    ]
                    with json_path.open("w", encoding="utf-8") as jh:
                        json.dump(row_dicts, jh, ensure_ascii=False, indent=2)
                console.print(f"[green]OK[/] {output_path}")
                progress.advance(listings_task)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
