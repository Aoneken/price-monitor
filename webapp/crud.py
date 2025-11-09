import logging
from datetime import date, datetime
from typing import List, Optional

import requests
from sqlalchemy.orm import Session

from price_monitor.core.calendar import build_daymap, fetch_calendar, month_count
from price_monitor.core.rows import build_rows
from price_monitor.providers.airbnb import COMMON_HEADERS
from webapp.models import (
    Listing,
    PlatformSource,
    PriceRecord,
    ScrapeJob,
    Season,
    Workspace,
)
from webapp.schemas import (
    ListingCreate,
    PlatformSourceCreate,
    ScrapeJobCreate,
    SeasonCreate,
    WorkspaceCreate,
)

logger = logging.getLogger("price_monitor.webapp.crud")


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
            workspace_id=listing_data.workspace_id,
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
    return listing


# Workspaces
def create_workspace(db: Session, data: WorkspaceCreate) -> Workspace:
    ws = Workspace(name=data.name)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    logger.info("workspace_created id=%s name=%s", ws.id, ws.name)
    return ws


def list_workspaces(db: Session) -> List[Workspace]:
    return db.query(Workspace).order_by(Workspace.created_at.desc()).all()


def create_season(db: Session, workspace_id: int, data: SeasonCreate) -> Season:
    season = Season(
        workspace_id=workspace_id,
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(season)
    db.commit()
    db.refresh(season)
    logger.info(
        "season_created id=%s workspace_id=%s range=%s-%s",
        season.id,
        workspace_id,
        season.start_date,
        season.end_date,
    )
    return season


def list_seasons(db: Session, workspace_id: int) -> List[Season]:
    return (
        db.query(Season)
        .filter(Season.workspace_id == workspace_id)
        .order_by(Season.created_at.desc())
        .all()
    )


def add_platform_source(
    db: Session, listing_id: int, data: PlatformSourceCreate
) -> PlatformSource:
    src = PlatformSource(
        listing_id=listing_id,
        platform=data.platform,
        base_url=data.base_url,
        extra_data=data.extra_data,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    logger.info(
        "platform_source_added listing_id=%s platform=%s", listing_id, data.platform
    )
    return src


def create_scrape_job(db: Session, job_data: ScrapeJobCreate) -> ScrapeJob:
    job = ScrapeJob(
        listing_id=job_data.listing_id,
        start_date=job_data.start_date,
        end_date=job_data.end_date,
        guests=job_data.guests,
        provider=job_data.provider,
        status="pending",
        season_id=job_data.season_id,
        params=job_data.params,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(
        "scrape_job_created id=%s listing_id=%s provider=%s range=%s-%s",
        job.id,
        job.listing_id,
        job.provider,
        job.start_date,
        job.end_date,
    )
    return job


def run_scrape_job(db: Session, job: ScrapeJob):
    """Execute scrape job and store results in database."""
    try:
        # Mark as running
        setattr(job, "status", "running")  # type: ignore[attr-defined]
        setattr(job, "progress", 0)  # type: ignore[attr-defined]
        setattr(job, "current_step", "Iniciando...")  # type: ignore[attr-defined]
        db.commit()
        logger.info(
            "scrape_job_started id=%s listing_id=%s provider=%s range=%s-%s",
            job.id,
            job.listing_id,
            job.provider,
            job.start_date,
            job.end_date,
        )

        # Resolve listing
        setattr(job, "current_step", "Resolviendo establecimiento...")  # type: ignore[attr-defined]
        setattr(job, "progress", 5)  # type: ignore[attr-defined]
        db.commit()
        listing = db.query(Listing).filter(Listing.id == job.listing_id).first()
        if not listing:
            raise ValueError("Listing not found")

        # Provider branching (currently only Airbnb supported)
        provider_value: str = str(getattr(job, "provider") or "airbnb")
        if provider_value != "airbnb":
            setattr(job, "status", "failed")  # type: ignore[attr-defined]
            setattr(
                job, "error", f"provider_not_supported:{provider_value}"
            )  # type: ignore[attr-defined]
            db.commit()
            logger.warning(
                "scrape_job_failed id=%s reason=provider_not_supported provider=%s",
                job.id,
                provider_value,
            )
            return

        # Fetch calendar (Airbnb)
        setattr(job, "current_step", "Obteniendo calendario...")  # type: ignore[attr-defined]
        setattr(job, "progress", 20)  # type: ignore[attr-defined]
        db.commit()

        session = requests.Session()
        session.headers.update(COMMON_HEADERS)

        total_months = month_count(
            job.start_date, job.end_date  # type: ignore[arg-type]
        )
        listing_identifier = str(getattr(listing, "listing_id"))
        calendar_data = fetch_calendar(
            session,
            listing_identifier,
            job.start_date.month,
            job.start_date.year,
            total_months,
            locale=(job.params or {}).get("locale", "en"),
            currency=(job.params or {}).get("currency", "USD"),
            retries=3,
            delay=0.5,
        )

        setattr(job, "current_step", "Procesando calendario...")  # type: ignore[attr-defined]
        setattr(job, "progress", 40)  # type: ignore[attr-defined]
        db.commit()

        daymap = build_daymap(calendar_data)

        # Build rows (no caching for fresh scrape)
        setattr(job, "current_step", "Obteniendo precios detallados...")  # type: ignore[attr-defined]
        setattr(job, "progress", 50)  # type: ignore[attr-defined]
        db.commit()

        rows = build_rows(
            session,
            listing_identifier,  # type: ignore[arg-type]
            job.start_date,  # type: ignore[arg-type]
            job.end_date,  # type: ignore[arg-type]
            job.guests,  # type: ignore[arg-type]
            daymap,
            (job.params or {}).get("currency", "USD"),
            (job.params or {}).get("locale", "en"),
            float((job.params or {}).get("delay", 0.4)),
            int((job.params or {}).get("retries", 2)),
            int((job.params or {}).get("cache_hours", 0)),
            (job.params or {}).get("feature_flags", {}),
            max_workers=int((job.params or {}).get("concurrency", 4)),
        )

        # Store in database
        setattr(job, "current_step", f"Guardando {len(rows)} registros...")  # type: ignore[attr-defined]
        setattr(job, "progress", 80)  # type: ignore[attr-defined]
        db.commit()

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
                currency=row[10] or (job.params or {}).get("currency", "USD"),
                inserted_at=(
                    datetime.fromisoformat(row[11]) if row[11] else datetime.utcnow()
                ),
                notes=row[12] or "",
                job_id=job.id,
            )
            db.add(record)

        setattr(job, "status", "completed")  # type: ignore[attr-defined]
        setattr(job, "progress", 100)  # type: ignore[attr-defined]
        setattr(job, "current_step", "Completado")  # type: ignore[attr-defined]
        setattr(job, "completed_at", datetime.utcnow())  # type: ignore[attr-defined]
        db.commit()
        logger.info("scrape_job_completed id=%s records=%s", job.id, len(rows))

    except Exception as exc:
        setattr(job, "status", "failed")  # type: ignore[attr-defined]
        setattr(job, "progress", 0)  # type: ignore[attr-defined]
        setattr(job, "current_step", f"Error: {str(exc)[:100]}")  # type: ignore[attr-defined]
        setattr(job, "error", str(exc)[:500])  # type: ignore[attr-defined]
        db.commit()
        logger.exception("scrape_job_exception id=%s error=%s", job.id, exc)
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


def export_snapshots_csv(
    db: Session,
    season_id: Optional[int],
    listing_id: Optional[int],
    start_date: date,
    end_date: date,
) -> List[List[str]]:
    q = db.query(PriceRecord)
    if listing_id:
        q = q.filter(PriceRecord.listing_id == listing_id)
    q = q.filter(PriceRecord.date >= start_date, PriceRecord.date <= end_date)
    if season_id:
        q = q.join(ScrapeJob, PriceRecord.job_id == ScrapeJob.id).filter(
            ScrapeJob.season_id == season_id
        )
    rows: List[List[str]] = []
    for r in q.order_by(PriceRecord.date).all():
        csv_row: List[str] = [
            r.date.isoformat(),
            str(r.available) if r.available is not None else "",
            str(r.available_for_checkin) if r.available_for_checkin is not None else "",
            (
                str(r.available_for_checkout)
                if r.available_for_checkout is not None
                else ""
            ),
            str(r.bookable) if r.bookable is not None else "",
            str(r.min_nights) if r.min_nights is not None else "",
            str(r.max_nights) if r.max_nights is not None else "",
            f"{r.price_per_night:.2f}" if r.price_per_night is not None else "",
            str(r.price_basis_nights) if r.price_basis_nights is not None else "",
            f"{r.stay_total:.2f}" if r.stay_total is not None else "",
            str(r.currency) if r.currency is not None else "",
            (r.inserted_at or datetime.utcnow()).isoformat(),
            r.notes or "",
        ]
        rows.append(csv_row)
    return rows
