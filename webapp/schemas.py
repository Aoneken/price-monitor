from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class ListingBase(BaseModel):
    listing_id: str
    name: str
    url: Optional[str] = None
    provider: str = "airbnb"


class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    id: int

    class Config:
        from_attributes = True


class PriceRecordResponse(BaseModel):
    id: int
    date: date
    available: Optional[bool]
    available_for_checkin: Optional[bool]
    available_for_checkout: Optional[bool]
    bookable: Optional[bool]
    min_nights: Optional[int]
    max_nights: Optional[int]
    price_per_night: Optional[float]
    price_basis_nights: Optional[int]
    stay_total: Optional[float]
    currency: str
    notes: Optional[str]

    class Config:
        from_attributes = True


class ScrapeJobCreate(BaseModel):
    listing_id: int
    start_date: date
    end_date: date
    guests: int = 2


class ScrapeJobResponse(BaseModel):
    id: int
    listing_id: int
    start_date: date
    end_date: date
    guests: int
    status: str
    error: Optional[str] = None

    class Config:
        from_attributes = True
