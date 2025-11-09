import asyncio
import csv
import logging
import os
import time
from datetime import date
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from webapp import crud
from webapp.database import (
    SessionLocal,
    get_db,
    init_db,
)
from webapp.logging_config import init_logging
from webapp.models import Listing, PlatformSource, ScrapeJob, Workspace
from webapp.schemas import (
    ListingCreate,
    ListingResponse,
    PlatformSourceCreate,
    PlatformSourceResponse,
    PriceRecordResponse,
    ScrapeJobCreate,
    ScrapeJobResponse,
    SeasonCreate,
    SeasonResponse,
    WorkspaceCreate,
    WorkspaceResponse,
)

app = FastAPI(title="Price Monitor API")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


def _extract_airbnb_listing_id(url: str) -> str | None:
    try:
        if not url:
            return None
        # Expecting .../rooms/<id>(?...)
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p]
        if "rooms" in parts:
            idx = parts.index("rooms")
            if idx + 1 < len(parts):
                # listing id is next segment
                return parts[idx + 1]
        return None
    except Exception:
        return None


def _autoload_establishments() -> int:
    """Load listings from CSV if available.

    Returns number of inserted listings.
    """
    logger = logging.getLogger("price_monitor.webapp.startup")
    project_root = os.path.dirname(os.path.dirname(__file__))

    # Try multiple locations for establecimientos.csv
    candidates = [
        os.path.join(project_root, "data", "establecimientos.csv"),
        os.path.join(project_root, "tests", "fixtures", "establecimientos.csv"),
        os.path.join(project_root, "establecimientos.csv"),
    ]
    csv_path = None
    for candidate in candidates:
        if os.path.exists(candidate):
            csv_path = candidate
            break
    if not os.path.exists(csv_path):
        logger.info("autoload_csv_missing path=%s", csv_path)
        return 0

    inserted = 0
    db = SessionLocal()
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("Establecimiento") or "").strip().strip('"')
                airbnb_url = (row.get("Airbnb") or "").strip()
                listing_id = _extract_airbnb_listing_id(airbnb_url)
                if not name or not airbnb_url or not listing_id:
                    continue
                # Insert if not exists
                existing = (
                    db.query(Listing).filter(Listing.listing_id == listing_id).first()
                )
                if existing:
                    continue
                payload = ListingCreate(
                    listing_id=listing_id,
                    name=name,
                    url=airbnb_url,
                    provider="airbnb",
                )
                crud.get_or_create_listing(db, payload)
                inserted += 1
        logger.info("autoload_csv_success inserted=%s path=%s", inserted, csv_path)
        return inserted
    except Exception as exc:
        logger.exception("autoload_csv_error path=%s error=%s", csv_path, exc)
        return inserted
    finally:
        db.close()


# ========================================
# DATABASE EXPLORER ENDPOINTS
# ========================================


@app.get("/api/database/prices")
def get_database_prices(
    page: int = 1,
    page_size: int = 50,
    listing_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    season_id: Optional[int] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get paginated price records with filters"""
    from webapp.models import PriceRecord

    query = db.query(PriceRecord).join(Listing)

    # Apply filters
    if listing_id:
        query = query.filter(PriceRecord.listing_id == listing_id)
    if workspace_id:
        query = query.filter(Listing.workspace_id == workspace_id)
    if date_start:
        query = query.filter(PriceRecord.date >= date_start)
    if date_end:
        query = query.filter(PriceRecord.date <= date_end)

    # Get total count
    total = query.count()

    # Apply sorting
    if sort_by:
        column = getattr(PriceRecord, sort_by, None)
        if column is not None:
            query = query.order_by(
                column.desc() if sort_order == "desc" else column.asc()
            )
        else:
            query = query.order_by(PriceRecord.date.desc())
    else:
        query = query.order_by(PriceRecord.date.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Convert to dict with listing name
    results = []
    for item in items:
        listing = db.query(Listing).filter(Listing.id == item.listing_id).first()
        results.append(
            {
                "id": item.id,
                "listing_id": item.listing_id,
                "listing_name": listing.name if listing else f"ID: {item.listing_id}",
                "date": str(item.date),
                "available": item.available,
                "available_for_checkin": item.available_for_checkin,
                "available_for_checkout": item.available_for_checkout,
                "bookable": item.bookable,
                "min_nights": item.min_nights,
                "max_nights": item.max_nights,
                "price_per_night": item.price_per_night,
                "stay_total": item.stay_total,
                "currency": item.currency,
                "inserted_at": str(item.inserted_at) if item.inserted_at else None,
            }
        )

    return {"total": total, "items": results, "page": page, "page_size": page_size}


@app.get("/api/database/listings")
def get_database_listings(
    page: int = 1,
    page_size: int = 50,
    workspace_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get paginated listings with filters"""
    query = db.query(Listing)

    if workspace_id:
        query = query.filter(Listing.workspace_id == workspace_id)

    total = query.count()

    # Apply sorting
    if sort_by:
        column = getattr(Listing, sort_by, None)
        if column is not None:
            query = query.order_by(
                column.desc() if sort_order == "desc" else column.asc()
            )
        else:
            query = query.order_by(Listing.id)
    else:
        query = query.order_by(Listing.id)

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    results = []
    for item in items:
        results.append(
            {
                "id": item.id,
                "listing_id": item.listing_id,
                "name": item.name,
                "url": item.url,
                "provider": item.provider,
                "workspace_id": item.workspace_id,
            }
        )

    return {"total": total, "items": results, "page": page, "page_size": page_size}


@app.get("/api/database/jobs")
def get_database_jobs(
    page: int = 1,
    page_size: int = 50,
    listing_id: Optional[int] = None,
    status: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get paginated scrape jobs with filters"""
    query = db.query(ScrapeJob)

    if listing_id:
        query = query.filter(ScrapeJob.listing_id == listing_id)
    if status:
        query = query.filter(ScrapeJob.status == status)
    if date_start:
        query = query.filter(ScrapeJob.start_date >= date_start)
    if date_end:
        query = query.filter(ScrapeJob.end_date <= date_end)

    total = query.count()

    # Apply sorting
    if sort_by:
        column = getattr(ScrapeJob, sort_by, None)
        if column is not None:
            query = query.order_by(
                column.desc() if sort_order == "desc" else column.asc()
            )
        else:
            query = query.order_by(ScrapeJob.id.desc())
    else:
        query = query.order_by(ScrapeJob.id.desc())

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    results = []
    for item in items:
        results.append(
            {
                "id": item.id,
                "listing_id": item.listing_id,
                "start_date": str(item.start_date),
                "end_date": str(item.end_date),
                "guests": item.guests,
                "provider": item.provider,
                "status": item.status,
                "error": item.error,
                "created_at": str(item.created_at) if item.created_at else None,
                "completed_at": str(item.completed_at) if item.completed_at else None,
            }
        )

    return {"total": total, "items": results, "page": page, "page_size": page_size}


@app.get("/api/database/seasons")
def get_database_seasons(
    page: int = 1,
    page_size: int = 50,
    workspace_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    """Get paginated seasons with filters"""
    from webapp.models import Season

    query = db.query(Season)

    if workspace_id:
        query = query.filter(Season.workspace_id == workspace_id)

    total = query.count()

    # Apply sorting
    if sort_by:
        column = getattr(Season, sort_by, None)
        if column is not None:
            query = query.order_by(
                column.desc() if sort_order == "desc" else column.asc()
            )
        else:
            query = query.order_by(Season.id.desc())
    else:
        query = query.order_by(Season.id.desc())

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    results = []
    for item in items:
        results.append(
            {
                "id": item.id,
                "workspace_id": item.workspace_id,
                "name": item.name,
                "start_date": str(item.start_date),
                "end_date": str(item.end_date),
                "created_at": str(item.created_at) if item.created_at else None,
            }
        )

    return {"total": total, "items": results, "page": page, "page_size": page_size}


@app.delete("/api/database/prices")
def delete_filtered_prices(
    listing_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    season_id: Optional[int] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Delete price records matching the provided filters"""
    from webapp.models import PriceRecord

    query = db.query(PriceRecord)

    # Apply the same filters as in get_database_prices
    if listing_id:
        query = query.filter(PriceRecord.listing_id == listing_id)
    if workspace_id:
        query = query.join(Listing).filter(Listing.workspace_id == workspace_id)
    if date_start:
        query = query.filter(PriceRecord.date >= date_start)
    if date_end:
        query = query.filter(PriceRecord.date <= date_end)

    # Count before deletion
    count = query.count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No records found matching filters")

    # Delete matching records
    query.delete(synchronize_session=False)
    db.commit()

    return {
        "message": f"Successfully deleted {count} price records",
        "deleted_count": count,
    }


@app.delete("/api/database/listings")
def delete_filtered_listings(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Delete listings matching the provided filters"""
    query = db.query(Listing)

    if workspace_id:
        query = query.filter(Listing.workspace_id == workspace_id)

    count = query.count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No records found matching filters")

    # Delete matching records
    query.delete(synchronize_session=False)
    db.commit()

    return {"message": f"Successfully deleted {count} listings", "deleted_count": count}


@app.delete("/api/database/jobs")
def delete_filtered_jobs(
    workspace_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Delete scrape jobs matching the provided filters"""
    query = db.query(ScrapeJob)

    if workspace_id:
        query = query.filter(ScrapeJob.workspace_id == workspace_id)
    if status:
        query = query.filter(ScrapeJob.status == status)

    count = query.count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No records found matching filters")

    # Delete matching records
    query.delete(synchronize_session=False)
    db.commit()

    return {"message": f"Successfully deleted {count} jobs", "deleted_count": count}


@app.delete("/api/database/seasons")
def delete_filtered_seasons(
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Delete seasons matching the provided filters"""
    from webapp.models import Season

    query = db.query(Season)

    if workspace_id:
        query = query.filter(Season.workspace_id == workspace_id)

    count = query.count()

    if count == 0:
        raise HTTPException(status_code=404, detail="No records found matching filters")

    # Delete matching records
    query.delete(synchronize_session=False)
    db.commit()

    return {"message": f"Successfully deleted {count} seasons", "deleted_count": count}


@app.on_event("startup")
def startup():
    # Skip startup initialization during testing
    if os.environ.get("TESTING"):
        return

    # Initialize logging early
    init_logging()
    init_db()
    # Optional: run lightweight SQLite schema adjustments if DB already exists
    try:
        from webapp.database import migrate_sqlite_schema

        migrate_sqlite_schema()
    except Exception:
        # Non-fatal; prefer to continue startup
        pass
    # Autoload listings from CSV if available
    _autoload_establishments()
    # Ensure a default workspace exists
    db = SessionLocal()
    try:
        default = db.query(Workspace).filter(Workspace.name == "Default").first()
        if not default:
            crud.create_workspace(db, WorkspaceCreate(name="Default"))
    finally:
        db.close()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("price_monitor.webapp.requests")
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# API Endpoints
@app.post("/api/listings", response_model=ListingResponse)
def create_listing(listing: ListingCreate, db: Session = Depends(get_db)):
    # Assign to default workspace if none provided
    if listing.workspace_id is None:
        default = db.query(Workspace).filter(Workspace.name == "Default").first()
        if default is not None:
            data = listing.model_dump()
            data["workspace_id"] = int(getattr(default, "id"))
            listing = ListingCreate(**data)
    return crud.get_or_create_listing(db, listing)


@app.get("/api/listings", response_model=List[ListingResponse])
def list_listings(workspace_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Listing).options(joinedload(Listing.platform_sources))
    if workspace_id:
        q = q.filter(Listing.workspace_id == workspace_id)
    return q.order_by(Listing.created_at.desc()).all()


@app.get("/api/listings/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@app.post("/api/scrape", response_model=ScrapeJobResponse)
def create_scrape(
    job_data: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = crud.create_scrape_job(db, job_data)
    background_tasks.add_task(crud.run_scrape_job, db, job)
    return job


@app.get("/api/jobs/{job_id}", response_model=ScrapeJobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/scrape-jobs", response_model=List[ScrapeJobResponse])
def list_scrape_jobs(db: Session = Depends(get_db)):
    """List all scrape jobs"""
    jobs = db.query(ScrapeJob).order_by(ScrapeJob.id.desc()).all()
    return jobs


@app.get("/api/scrape-jobs/{job_id}", response_model=ScrapeJobResponse)
def get_scrape_job(job_id: int, db: Session = Depends(get_db)):
    """Get specific scrape job"""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/prices/by-date")
def get_prices_by_date(
    start_date: date,
    end_date: date,
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get price data grouped by date for analytics.
    Returns data suitable for Chart.js time series.
    """
    from sqlalchemy import func
    from webapp.models import PriceRecord

    query = db.query(
        func.date(PriceRecord.date).label("date"),
        func.avg(PriceRecord.price_per_night).label("avg_price"),
        func.min(PriceRecord.price_per_night).label("min_price"),
        func.max(PriceRecord.price_per_night).label("max_price"),
        func.count(PriceRecord.id).label("count"),
    ).filter(
        PriceRecord.date >= start_date,
        PriceRecord.date <= end_date,
    )

    if workspace_id:
        query = query.join(Listing).filter(Listing.workspace_id == workspace_id)

    results = query.group_by(func.date(PriceRecord.date)).order_by("date").all()

    return [
        {
            "date": str(r.date),
            "avg_price": float(r.avg_price) if r.avg_price else 0,
            "min_price": float(r.min_price) if r.min_price else 0,
            "max_price": float(r.max_price) if r.max_price else 0,
            "count": r.count,
        }
        for r in results
    ]


@app.get("/api/prices/by-establishment")
def get_prices_by_establishment(
    start_date: date,
    end_date: date,
    workspace_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get price data grouped by establishment for analytics.
    Returns data suitable for Chart.js bar/pie charts.
    """
    from sqlalchemy import func
    from webapp.models import PriceRecord

    query = (
        db.query(
            Listing.id,
            Listing.name,
            func.avg(PriceRecord.price_per_night).label("avg_price"),
            func.min(PriceRecord.price_per_night).label("min_price"),
            func.max(PriceRecord.price_per_night).label("max_price"),
            func.count(PriceRecord.id).label("count"),
        )
        .join(PriceRecord)
        .filter(
            PriceRecord.date >= start_date,
            PriceRecord.date <= end_date,
        )
    )

    if workspace_id:
        query = query.filter(Listing.workspace_id == workspace_id)

    results = query.group_by(Listing.id, Listing.name).all()

    return [
        {
            "listing_id": r.id,
            "listing_name": r.name,
            "avg_price": float(r.avg_price) if r.avg_price else 0,
            "min_price": float(r.min_price) if r.min_price else 0,
            "max_price": float(r.max_price) if r.max_price else 0,
            "count": r.count,
        }
        for r in results
    ]


@app.get("/api/prices/{listing_id}", response_model=List[PriceRecordResponse])
def get_prices(
    listing_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    prices = crud.get_prices_for_listing(db, listing_id, start_date, end_date)
    return prices


@app.get("/api/seasons/{season_id}/snapshots")
def export_snapshots(
    season_id: int,
    listing_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=400, detail="date_from and date_to are required"
        )
    rows = crud.export_snapshots_csv(db, season_id, listing_id, date_from, date_to)

    def iter_csv():
        header = [
            "date",
            "available",
            "available_checkin",
            "available_checkout",
            "bookable",
            "min_nights",
            "max_nights",
            "price_per_night",
            "price_basis_nights",
            "stay_total",
            "currency",
            "inserted_at",
            "notes",
        ]
        yield ",".join(header) + "\n"
        for r in rows:
            yield ",".join(r) + "\n"

    filename = f"snapshots_season_{season_id}.csv"
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/seasons/{season_id}/scrape")
def create_season_scrape(
    season_id: int,
    data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Launch scrape jobs for a season with multiple establishments.

    Expected payload:
    {
        "establishments": [listing_id1, listing_id2, ...],
        "platform": "airbnb",
        "params": {
            "guests": 2,
            "currency": "USD",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31"
        }
    }

    Returns list of created jobs.
    """
    # Validate season exists
    from webapp.models import Season

    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    # Extract data
    establishment_ids = data.get("establishments", [])
    params = data.get("params", {})

    if not establishment_ids:
        raise HTTPException(status_code=400, detail="No establishments provided")

    # Create jobs for each establishment
    jobs = []
    for listing_id in establishment_ids:
        job_data = ScrapeJobCreate(
            listing_id=listing_id,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            guests=params.get("guests", 2),
            currency=params.get("currency", "USD"),
        )
        job = crud.create_scrape_job(db, job_data)
        background_tasks.add_task(crud.run_scrape_job, db, job)
        jobs.append(job)

    # Return first job id for WebSocket connection (monitor first job as representative)
    return {
        "id": jobs[0].id if jobs else None,
        "job_id": jobs[0].id if jobs else None,
        "jobs": [
            {"id": j.id, "listing_id": j.listing_id, "status": j.status} for j in jobs
        ],
        "total_jobs": len(jobs),
    }


@app.websocket("/ws/scrape-jobs/{job_id}")
async def websocket_scrape_job(websocket: WebSocket, job_id: int):
    await websocket.accept()
    try:
        # Poll job status until completion
        while True:
            db = SessionLocal()
            try:
                job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
                if not job:
                    await websocket.send_json(
                        {"type": "error", "message": "job_not_found"}
                    )
                    await websocket.close()
                    return

                status = str(getattr(job, "status"))
                progress = int(getattr(job, "progress", 0))
                current_step = str(getattr(job, "current_step", ""))

                payload = {
                    "id": job.id,
                    "status": status,
                    "progress": progress,
                    "current_step": current_step,
                    "error": job.error,
                    "completed_at": (
                        job.completed_at.isoformat()
                        if getattr(job, "completed_at") is not None
                        else None
                    ),
                }

                # Send progress update
                await websocket.send_json(
                    {
                        "type": "progress",
                        "percent": progress,
                        "log": current_step,
                        "status": status,
                        "job": payload,
                    }
                )

                if status in ("completed", "failed"):
                    await websocket.send_json(
                        {
                            "type": "done" if status == "completed" else "error",
                            "status": status,
                            "job": payload,
                        }
                    )
                    await websocket.close()
                    return
            finally:
                db.close()
            await asyncio.sleep(0.5)  # Poll every 500ms for more responsive updates
    except WebSocketDisconnect:
        return


# Workspaces & Seasons
@app.post("/api/workspaces", response_model=WorkspaceResponse)
def create_workspace(data: WorkspaceCreate, db: Session = Depends(get_db)):
    return crud.create_workspace(db, data)


@app.get("/api/workspaces", response_model=List[WorkspaceResponse])
def list_workspaces(db: Session = Depends(get_db)):
    return crud.list_workspaces(db)


@app.get("/api/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


@app.put("/api/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int, data: WorkspaceCreate, db: Session = Depends(get_db)
):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    ws.name = data.name
    db.commit()
    db.refresh(ws)
    return ws


@app.delete("/api/workspaces/{workspace_id}")
def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    db.delete(ws)
    db.commit()
    return {"message": "Workspace deleted"}


@app.post("/api/workspaces/{workspace_id}/seasons", response_model=SeasonResponse)
def create_workspace_season(
    workspace_id: int, data: SeasonCreate, db: Session = Depends(get_db)
):
    # Validate workspace exists
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return crud.create_season(db, workspace_id, data)


@app.get(
    "/api/workspaces/{workspace_id}/seasons",
    response_model=List[SeasonResponse],
)
def list_workspace_seasons(workspace_id: int, db: Session = Depends(get_db)):
    return crud.list_seasons(db, workspace_id)


@app.delete("/api/seasons/{season_id}")
def delete_season(season_id: int, db: Session = Depends(get_db)):
    from webapp.models import Season

    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    db.delete(season)
    db.commit()
    return {"message": "Season deleted"}


@app.delete("/api/listings/{listing_id}")
def delete_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted"}


# Platform Sources
@app.post(
    "/api/listings/{listing_id}/platform-sources",
    response_model=PlatformSourceResponse,
)
def create_platform_source(
    listing_id: int, data: PlatformSourceCreate, db: Session = Depends(get_db)
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return crud.add_platform_source(db, listing_id, data)


@app.get(
    "/api/listings/{listing_id}/platform-sources",
    response_model=List[PlatformSourceResponse],
)
def list_platform_sources(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return (
        db.query(PlatformSource)
        .filter(PlatformSource.listing_id == listing_id)
        .order_by(PlatformSource.created_at.desc())
        .all()
    )


# Web UI
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    workspaces = db.query(Workspace).order_by(Workspace.created_at.desc()).all()
    active_workspace_id = int(getattr(workspaces[0], "id")) if workspaces else None
    if active_workspace_id is not None:
        seasons = crud.list_seasons(db, int(active_workspace_id))
        listings = (
            db.query(Listing)
            .filter(Listing.workspace_id == int(active_workspace_id))
            .order_by(Listing.created_at.desc())
            .all()
        )
    else:
        seasons = []
        listings = []
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "listings": listings,
            "workspaces": workspaces,
            "seasons": seasons,
            "active_workspace_id": active_workspace_id,
        },
    )


@app.get("/listing/{listing_id}", response_class=HTMLResponse)
def listing_detail(request: Request, listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    seasons = []
    if getattr(listing, "workspace_id") is not None:
        seasons = crud.list_seasons(db, int(getattr(listing, "workspace_id")))
    return templates.TemplateResponse(
        "listing.html",
        {"request": request, "listing": listing, "seasons": seasons},
    )
