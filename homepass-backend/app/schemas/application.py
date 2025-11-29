from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ApplicationItemSchema(BaseModel):
    application_id: int
    announcement_id: int
    announcement_title: str
    status: str
    applied_at: Optional[datetime] = None
    status_updated_at: Optional[datetime] = None
    dday: Optional[int] = None
    housing_type: Optional[str] = None
    region: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    total: int
    items: List[ApplicationItemSchema] = Field(default_factory=list)

