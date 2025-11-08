from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CSV_COLUMNS = [
    "date",
    "available",
    "availableForCheckin",
    "availableForCheckout",
    "bookable",
    "minNights",
    "maxNights",
    "pricePerNight",
    "priceBasisNights",
    "stayTotal",
    "currency",
    "insertedAt",
    "notes",
]

INSERTED_AT_INDEX = CSV_COLUMNS.index("insertedAt")


def load_existing_rows(output_path: Path) -> Dict[date, Dict[str, Any]]:
    if not output_path.exists():
        return {}

    existing: Dict[date, Dict[str, Any]] = {}
    with output_path.open("r", encoding="utf-8", newline="") as handle:

        def data_lines():
            for raw_line in handle:
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                yield raw_line

        reader = csv.reader(data_lines())
        header = next(reader, None)
        if not header:
            return {}

        header_map = {name: idx for idx, name in enumerate(header)}

        for row in reader:
            if not row:
                continue
            normalized = ["" for _ in CSV_COLUMNS]
            for name, idx in header_map.items():
                if name not in CSV_COLUMNS:
                    continue
                if idx < len(row):
                    normalized[CSV_COLUMNS.index(name)] = row[idx]

            try:
                row_date = date.fromisoformat(normalized[0])
            except ValueError:
                continue

            inserted_dt: Optional[datetime] = None
            inserted_str = normalized[INSERTED_AT_INDEX]
            if inserted_str:
                try:
                    inserted_dt = datetime.fromisoformat(inserted_str)
                except ValueError:
                    inserted_dt = None

            existing[row_date] = {"row": normalized, "inserted_at": inserted_dt}

    return existing


def write_csv(
    output_path: Path,
    listing_name: str,
    listing_id: str,
    listing_url: str,
    start_date: date,
    end_date: date,
    guests: int,
    rows: List[List[str]],
    cache_hours: float,
    existing_rows: Dict[date, Dict[str, Any]],
    freeze_before: date | None = None,
):
    today = date.today()
    freeze_boundary = min(today, freeze_before) if freeze_before else today
    frozen_rows: Dict[date, List[str]] = {
        day: info.get("row", [])
        for day, info in existing_rows.items()
        if day < freeze_boundary
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"# Listing: {listing_name}\n")
        handle.write(f"# Listing ID: {listing_id}\n")
        handle.write(f"# Listing URL: {listing_url}\n")
        handle.write(f"# Period: {start_date.isoformat()} to {end_date.isoformat()}\n")
        handle.write(f"# Guests: {guests}\n")
        handle.write(f"# Generated: {datetime.now().isoformat()}\n")
        handle.write(f"# Cache Hours: {cache_hours}\n")
        if freeze_before:
            handle.write(f"# Freeze Before: {freeze_before.isoformat()}\n")
        handle.write("#\n")
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            try:
                row_day = date.fromisoformat(row[0])
            except ValueError:
                writer.writerow(row)
                continue

            if row_day < freeze_boundary and row_day in frozen_rows:
                writer.writerow(frozen_rows[row_day])
            else:
                writer.writerow(row)
