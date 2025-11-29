from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AnnouncementSchema(BaseModel):
    announcement_id: int
    title: str
    housing_type: Optional[str] = None
    region: Optional[str] = None
    address_detail: Optional[str] = None
    source_organization: Optional[str] = None
    source_url: Optional[str] = None
    original_pdf_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    application_end_date: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    post_date: Optional[datetime] = None
    min_deposit: Optional[int] = None
    max_deposit: Optional[int] = None
    monthly_rent: Optional[int] = None
    total_households: Optional[int] = None
    eligibility: Optional[str] = None
    commute_base_address: Optional[str] = None
    commute_time: Optional[int] = None
    image_urls: List[str] = Field(default_factory=list)
    is_customized: bool = False
    dday: Optional[int] = None

    class Config:
        from_attributes = True


class AnnouncementDetailSchema(AnnouncementSchema):
    schedules: List[dict] = Field(default_factory=list)


class AnnouncementListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AnnouncementSchema]

