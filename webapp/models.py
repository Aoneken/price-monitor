from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String)
    provider = Column(String, default="airbnb")
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship(
        "PriceRecord", back_populates="listing", cascade="all, delete-orphan"
    )


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

    listing = relationship("Listing", back_populates="prices")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    guests = Column(Integer, default=2)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error = Column(Text)

    listing = relationship("Listing")
