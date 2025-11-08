#!/usr/bin/env python3
"""Batch processor for all Airbnb listings from establecimientos.csv.

This script reads establecimientos.csv and generates a pricing/availability
table for each Airbnb listing found. Each establishment gets its own CSV file
in the output directory.

Usage:
    python3 get_all_prices.py --start 2025-12-01 --end 2026-03-31 --guests 2

    # With fixed rate pricing:
    python3 get_all_prices.py --start 2025-12-01 --end 2026-03-31 --guests 2 --fixed-rate 150

    # Specify custom paths:
    python3 get_all_prices.py --start 2025-12-01 --end 2026-03-31 --guests 2 \\
        --csv ../../establecimientos/establecimientos.csv \\
        --output-dir ./output

Output:
    Creates one CSV per establishment in output directory:
    - output/Aizeder_2025-12-01_2026-03-31.csv
    - output/Patagonia_Eco_Domes_2025-12-01_2026-03-31.csv
    - etc.
"""

import argparse
import csv
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import List, Dict


def parse_establecimientos_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Parse establecimientos.csv and return list of Airbnb listings.

    Returns: List of dicts with keys: Establecimiento, Airbnb (URL), listing_id
    """
    listings = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            airbnb_url = row.get("Airbnb", "").strip()
            establecimiento = row.get("Establecimiento", "").strip()

            if not airbnb_url or not establecimiento:
                continue

            # Extract listing ID from URL
            # Format: https://www.airbnb.com.ar/rooms/928978094650118177
            if "/rooms/" in airbnb_url:
                listing_id = airbnb_url.split("/rooms/")[-1].split("?")[0].strip()
                if listing_id:
                    listings.append({
                        "Establecimiento": establecimiento,
                        "Airbnb": airbnb_url,
                        "listing_id": listing_id,
                    })

    return listings


def sanitize_filename(name: str) -> str:
    """Convert establishment name to safe filename."""
    # Replace spaces and special chars
    safe = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    # Remove other problematic chars
    safe = "".join(c for c in safe if c.isalnum() or c in ("_", "-"))
    return safe


def process_listing(
    listing: Dict[str, str],
    start_date: date,
    end_date: date,
    guests: int,
    output_dir: Path,
    script_path: Path,
    fixed_rate: float | None = None,
    csv_path: Path | None = None,
) -> bool:
    """Run get_prices_simple.py for a single listing.

    Returns: True if successful, False otherwise
    """
    establecimiento = listing["Establecimiento"]
    listing_id = listing["listing_id"]

    # Generate output filename
    safe_name = sanitize_filename(establecimiento)
    output_file = output_dir / f"{safe_name}_{start_date}_{end_date}.csv"

    print(f"\n{'=' * 70}")
    print(f"Processing: {establecimiento}")
    print(f"Listing ID: {listing_id}")
    print(f"Output: {output_file}")
    print(f"{'=' * 70}")

    # Build command
    cmd = [
        sys.executable,
        str(script_path),
        "--listing-id", listing_id,
        "--start", str(start_date),
        "--end", str(end_date),
        "--guests", str(guests),
        "--out", str(output_file),
    ]

    if fixed_rate is not None:
        cmd.extend(["--fixed-rate", str(fixed_rate)])

    if csv_path:
        cmd.extend(["--establecimientos-csv", str(csv_path)])

    # Run subprocess
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        print(result.stderr)
        print(f"✓ Success: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error processing {establecimiento}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout processing {establecimiento}", file=sys.stderr)
        return False


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Batch process all Airbnb listings from establecimientos.csv",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    p.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    p.add_argument(
        "--end",
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    p.add_argument(
        "--guests",
        type=int,
        default=2,
        help="Number of guests (default: 2)",
    )
    p.add_argument(
        "--csv",
        type=Path,
        help="Path to establecimientos.csv (auto-detected if not provided)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for CSV files (default: ./output)",
    )
    p.add_argument(
        "--fixed-rate",
        type=float,
        help="Fixed nightly rate to apply to all listings (optional)",
    )

    args = p.parse_args(argv)

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)

    # Find establecimientos.csv
    csv_path = args.csv
    if not csv_path:
        script_dir = Path(__file__).parent
        candidates = [
            script_dir / "../../establecimientos/establecimientos.csv",
            script_dir / "../establecimientos/establecimientos.csv",
            Path.cwd() / "establecimientos/establecimientos.csv",
            Path.cwd() / "Foco_01/Temp-25-26/establecimientos/establecimientos.csv",
        ]
        for candidate in candidates:
            if candidate.exists():
                csv_path = candidate
                break

    if not csv_path or not csv_path.exists():
        print(f"Error: Could not find establecimientos.csv", file=sys.stderr)
        print(f"Tried: {candidates if not args.csv else [args.csv]}", file=sys.stderr)
        return 1

    print(f"Using establecimientos CSV: {csv_path}")

    # Parse listings
    listings = parse_establecimientos_csv(csv_path)
    if not listings:
        print("Error: No Airbnb listings found in CSV", file=sys.stderr)
        return 1

    print(f"Found {len(listings)} Airbnb listings to process")

    # Create output directory
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir.resolve()}")

    # Find the get_prices_simple.py script
    script_dir = Path(__file__).parent
    script_path = script_dir / "copilot_tests/scripts/get_prices_simple.py"
    if not script_path.exists():
        print(f"Error: Could not find get_prices_simple.py at {script_path}", file=sys.stderr)
        return 1

    # Process each listing
    successes = 0
    failures = 0

    for listing in listings:
        success = process_listing(
            listing,
            start_date,
            end_date,
            args.guests,
            output_dir,
            script_path,
            fixed_rate=args.fixed_rate,
            csv_path=csv_path,
        )
        if success:
            successes += 1
        else:
            failures += 1

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total listings: {len(listings)}")
    print(f"Successful: {successes}")
    print(f"Failed: {failures}")
    print(f"\nOutput files in: {output_dir.resolve()}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
