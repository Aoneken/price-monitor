#!/usr/bin/env python3
"""Script to populate platform_sources table from establecimientos.csv"""

import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webapp.database import SessionLocal
from webapp.models import Listing, PlatformSource


def extract_id_from_url(url, platform):
    """Extract listing ID from URL"""
    if not url:
        return None

    if platform == "airbnb":
        # https://www.airbnb.com.ar/rooms/20754903
        parts = url.split("/rooms/")
        if len(parts) > 1:
            return parts[1].split("?")[0]
    elif platform == "booking":
        # https://www.booking.com/hotel/ar/patagonia-eco-domes.es.html
        parts = url.split("/hotel/ar/")
        if len(parts) > 1:
            slug = parts[1].split(".")[0]
            return slug
    elif platform == "expedia":
        # Extract hotel code from URL
        if ".h" in url:
            parts = url.split(".h")
            if len(parts) > 1:
                code = parts[1].split(".")[0]
                return f"h{code}"

    return None


def main():
    db = SessionLocal()

    try:
        # Read CSV
        csv_path = Path(__file__).parent.parent / "data" / "establecimientos.csv"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            establishments = list(reader)

        print(f"📖 Leyendo {len(establishments)} establecimientos del CSV\n")

        for row in establishments:
            name = row["Establecimiento"].strip()
            booking_url = row["Booking"].strip() if row["Booking"].strip() else None
            airbnb_url = row["Airbnb"].strip() if row["Airbnb"].strip() else None
            expedia_url = row["Expedia"].strip() if row["Expedia"].strip() else None

            # Find listing by name
            listing = db.query(Listing).filter(Listing.name == name).first()

            if not listing:
                print(f"⚠️  {name} - No encontrado en BD, salteando...")
                continue

            print(f"🔄 {name} (ID: {listing.id})")

            # Clear existing platform sources
            db.query(PlatformSource).filter(
                PlatformSource.listing_id == listing.id
            ).delete()

            # Add Airbnb
            if airbnb_url:
                airbnb_id = extract_id_from_url(airbnb_url, "airbnb")
                ps = PlatformSource(
                    listing_id=listing.id,
                    platform="airbnb",
                    base_url=airbnb_url,
                    extra_data={"listing_id": airbnb_id, "supported": True},
                )
                db.add(ps)
                print(f"   ✓ Airbnb: {airbnb_id}")

            # Add Booking
            if booking_url:
                booking_id = extract_id_from_url(booking_url, "booking")
                ps = PlatformSource(
                    listing_id=listing.id,
                    platform="booking",
                    base_url=booking_url,
                    extra_data={"listing_id": booking_id, "supported": False},
                )
                db.add(ps)
                print(f"   ✓ Booking: {booking_id} (sin soporte)")

            # Add Expedia
            if expedia_url:
                expedia_id = extract_id_from_url(expedia_url, "expedia")
                ps = PlatformSource(
                    listing_id=listing.id,
                    platform="expedia",
                    base_url=expedia_url,
                    extra_data={"listing_id": expedia_id, "supported": False},
                )
                db.add(ps)
                print(f"   ✓ Expedia: {expedia_id} (sin soporte)")

            db.commit()
            print()

        print("✅ Proceso completado")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
