from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BookmarkToggleResponse(BaseModel):
    is_bookmarked: bool


class BookmarkItem(BaseModel):
    announcement_id: int
    title: str
    housing_type: Optional[str] = None
    region: Optional[str] = None
    image_url: Optional[str] = None
    application_end_date: Optional[datetime] = None


class BookmarkListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[BookmarkItem] = Field(default_factory=list)

