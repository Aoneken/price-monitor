from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    seasons = relationship(
        "Season", back_populates="workspace", cascade="all, delete-orphan"
    )
    listings = relationship(
        "Listing", back_populates="workspace", cascade="all, delete-orphan"
    )


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="seasons")
    jobs = relationship(
        "ScrapeJob", back_populates="season", cascade="all, delete-orphan"
    )


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String)
    provider = Column(String, default="airbnb")
    created_at = Column(DateTime, default=datetime.utcnow)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)

    prices = relationship(
        "PriceRecord", back_populates="listing", cascade="all, delete-orphan"
    )
    platform_sources = relationship(
        "PlatformSource",
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    workspace = relationship("Workspace", back_populates="listings")


class PlatformSource(Base):
    __tablename__ = "platform_sources"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    platform = Column(String, nullable=False)  # airbnb, booking, expedia
    base_url = Column(Text, nullable=False)
    extra_data = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="platform_sources")


class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    available = Column(Boolean)
    available_for_checkin = Column(Boolean)
    available_for_checkout = Column(Boolean)
    bookable = Column(Boolean)
    min_nights = Column(Integer)
    max_nights = Column(Integer)
    price_per_night = Column(Float)
    price_basis_nights = Column(Integer)
    stay_total = Column(Float)
    currency = Column(String, default="USD")
    inserted_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=True, index=True)

    listing = relationship("Listing", back_populates="prices")
    job = relationship("ScrapeJob", back_populates="price_records")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    guests = Column(Integer, default=2)
    provider = Column(String, default="airbnb")
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100 percentage
    current_step = Column(String)  # Description of current operation
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error = Column(Text)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=True)
    params = Column(JSON)  # raw params used for the job

    listing = relationship("Listing")
    season = relationship("Season", back_populates="jobs")
    price_records = relationship(
        "PriceRecord", back_populates="job", cascade="all, delete-orphan"
    )
