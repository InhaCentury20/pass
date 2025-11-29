from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NotificationSettingSchema(BaseModel):
    id: int
    user_id: int
    new_announcement: bool
    auto_apply_complete: bool
    dday: bool
    result: bool
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationSettingPayload(BaseModel):
    new_announcement: Optional[bool] = None
    auto_apply_complete: Optional[bool] = None
    dday: Optional[bool] = None
    result: Optional[bool] = None


class NotificationItemSchema(BaseModel):
    notification_id: int
    announcement_id: Optional[int] = None
    category: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None
    announcement_title: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationItemSchema]

