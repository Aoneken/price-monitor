#!/usr/bin/env python3
"""Script to add missing listings from establecimientos.csv to the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from webapp.database import SessionLocal  # noqa: E402
from webapp.models import Listing  # noqa: E402

# Missing establishments data from CSV
missing_listings = [
    {
        "name": "Puesto Cagliero",
        "booking_url": "https://www.booking.com/hotel/ar/puesto-cagliero-en-estancia-los-huemules.es.html",
        "expedia_url": "https://www.expedia.com/es/El-Chalten-Hoteles-Puesto-Cagliero-En-Estancia-Los-Huemules.h21347332.Informacion-Hotel",
        "airbnb_url": None,
        "provider": "booking",
        "listing_id": "puesto-cagliero-en-estancia-los-huemules",
    },
    {
        "name": "Bonanza Glamp Nature Exp.",
        "booking_url": "https://www.booking.com/hotel/ar/bonanza-glamp-nature-experience.es.html",
        "expedia_url": "https://www.expedia.com/es/El-Chalten-Hoteles-Bonanza-Glamp-Nature-Experience.h119278520.Informacion-Hotel",
        "airbnb_url": None,
        "provider": "booking",
        "listing_id": "bonanza-glamp-nature-experience",
    },
    {
        "name": "El Pilar",
        "booking_url": "https://www.booking.com/hotel/ar/el-pilar.es.html",
        "expedia_url": None,
        "airbnb_url": None,
        "provider": "booking",
        "listing_id": "el-pilar",
    },
    {
        "name": "Camping Bonanza",
        "booking_url": "https://www.booking.com/hotel/ar/bonanza-eco-aventura-camping.es.html",
        "expedia_url": None,
        "airbnb_url": None,
        "provider": "booking",
        "listing_id": "bonanza-eco-aventura-camping",
    },
]


def main():
    db = SessionLocal()
    try:
        for listing_data in missing_listings:
            # Check if already exists
            existing = (
                db.query(Listing).filter(Listing.name == listing_data["name"]).first()
            )

            if existing:
                print(f"✓ {listing_data['name']} ya existe (ID: {existing.id})")
                continue

            # Create new listing
            new_listing = Listing(
                listing_id=listing_data["listing_id"],
                name=listing_data["name"],
                url=listing_data["booking_url"],  # Primary URL
                provider=listing_data["provider"],
                workspace_id=1,  # Patagonia 2025 workspace
            )

            db.add(new_listing)
            db.commit()
            db.refresh(new_listing)

            print(f"✓ Agregado: {new_listing.name} (ID: {new_listing.id})")
            print(f"  - Booking: {listing_data['booking_url']}")
            if listing_data.get("expedia_url"):
                print(f"  - Expedia: {listing_data['expedia_url']}")
            if listing_data.get("airbnb_url"):
                print(f"  - Airbnb: {listing_data['airbnb_url']}")

        print("\n✓ Proceso completado")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
