from datetime import date
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from webapp.database import get_db, init_db
from webapp.models import Listing, ScrapeJob
from webapp.schemas import (
    ListingCreate,
    ListingResponse,
    ScrapeJobCreate,
    ScrapeJobResponse,
    PriceRecordResponse,
)
from webapp import crud

app = FastAPI(title="Price Monitor API")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


@app.on_event("startup")
def startup():
    init_db()


# API Endpoints
@app.post("/api/listings", response_model=ListingResponse)
def create_listing(listing: ListingCreate, db: Session = Depends(get_db)):
    return crud.get_or_create_listing(db, listing)


@app.get("/api/listings", response_model=List[ListingResponse])
def list_listings(db: Session = Depends(get_db)):
    return db.query(Listing).all()


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


@app.get("/api/prices/{listing_id}", response_model=List[PriceRecordResponse])
def get_prices(
    listing_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    prices = crud.get_prices_for_listing(db, listing_id, start_date, end_date)
    return prices


# Web UI
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    listings = db.query(Listing).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "listings": listings}
    )


@app.get("/listing/{listing_id}", response_class=HTMLResponse)
def listing_detail(request: Request, listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return templates.TemplateResponse(
        "listing.html", {"request": request, "listing": listing}
    )
