from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ListingBase(BaseModel):
    listing_id: str
    name: str
    url: Optional[str] = None
    provider: str = "airbnb"
    workspace_id: Optional[int] = None


class ListingCreate(ListingBase):
    pass


class ListingResponse(ListingBase):
    id: int
    platform_sources: List["PlatformSourceResponse"] = []

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
    job_id: Optional[int]

    class Config:
        from_attributes = True


class ScrapeJobCreate(BaseModel):
    listing_id: int
    start_date: date
    end_date: date
    guests: int = 2
    provider: str = "airbnb"
    season_id: Optional[int] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class ScrapeJobResponse(BaseModel):
    id: int
    listing_id: int
    start_date: date
    end_date: date
    guests: int
    provider: str
    status: str
    progress: Optional[int] = 0
    current_step: Optional[str] = None
    season_id: Optional[int]
    error: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class SeasonCreate(BaseModel):
    name: str
    start_date: date
    end_date: date


class SeasonResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    start_date: date
    end_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class PlatformSourceCreate(BaseModel):
    platform: str
    base_url: str
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class PlatformSourceResponse(BaseModel):
    id: int
    listing_id: int
    platform: str
    base_url: str
    extra_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
