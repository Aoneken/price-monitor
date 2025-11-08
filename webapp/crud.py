from datetime import date, datetime
from typing import List
import requests

from sqlalchemy.orm import Session

from webapp.models import Listing, PriceRecord, ScrapeJob
from webapp.schemas import ListingCreate, ScrapeJobCreate
from price_monitor.core.calendar import fetch_calendar, build_daymap, month_count
from price_monitor.core.rows import build_rows
from price_monitor.providers.airbnb import COMMON_HEADERS


def get_or_create_listing(db: Session, listing_data: ListingCreate) -> Listing:
    listing = (
        db.query(Listing).filter(Listing.listing_id == listing_data.listing_id).first()
    )
    if not listing:
        listing = Listing(
            listing_id=listing_data.listing_id,
            name=listing_data.name,
            url=listing_data.url,
            provider=listing_data.provider,
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
    return listing


def create_scrape_job(db: Session, job_data: ScrapeJobCreate) -> ScrapeJob:
    job = ScrapeJob(
        listing_id=job_data.listing_id,
        start_date=job_data.start_date,
        end_date=job_data.end_date,
        guests=job_data.guests,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_scrape_job(db: Session, job: ScrapeJob):
    """Execute scrape job and store results in database."""
    try:
        job.status = "running"
        db.commit()

        listing = db.query(Listing).filter(Listing.id == job.listing_id).first()
        if not listing:
            raise ValueError("Listing not found")

        # Fetch calendar
        session = requests.Session()
        session.headers.update(COMMON_HEADERS)

        total_months = month_count(job.start_date, job.end_date)
        calendar_data = fetch_calendar(
            session,
            listing.listing_id,
            job.start_date.month,
            job.start_date.year,
            total_months,
            locale="en",
            currency="USD",
            retries=3,
            delay=0.5,
        )
        daymap = build_daymap(calendar_data)

        # Build rows (no caching for fresh scrape)
        rows = build_rows(
            session,
            listing.listing_id,
            job.start_date,
            job.end_date,
            job.guests,
            daymap,
            "USD",
            "en",
            0.4,
            2,
            0,  # cache_hours=0
            {},  # existing_rows={}
            max_workers=4,
        )

        # Store in database
        for row in rows:
            record = PriceRecord(
                listing_id=listing.id,
                date=date.fromisoformat(row[0]),
                available=row[1] == "True" if row[1] else None,
                available_for_checkin=row[2] == "True" if row[2] else None,
                available_for_checkout=row[3] == "True" if row[3] else None,
                bookable=row[4] == "True" if row[4] else None,
                min_nights=int(row[5]) if row[5] else None,
                max_nights=int(row[6]) if row[6] else None,
                price_per_night=float(row[7]) if row[7] else None,
                price_basis_nights=int(row[8]) if row[8] else None,
                stay_total=float(row[9]) if row[9] else None,
                currency=row[10] or "USD",
                inserted_at=(
                    datetime.fromisoformat(row[11]) if row[11] else datetime.utcnow()
                ),
                notes=row[12] or "",
            )
            db.add(record)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)[:500]
        db.commit()
        raise


def get_prices_for_listing(
    db: Session, listing_id: int, start_date: date, end_date: date
) -> List[PriceRecord]:
    return (
        db.query(PriceRecord)
        .filter(
            PriceRecord.listing_id == listing_id,
            PriceRecord.date >= start_date,
            PriceRecord.date <= end_date,
        )
        .order_by(PriceRecord.date)
        .all()
    )
