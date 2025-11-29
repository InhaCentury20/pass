from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionInfoSchema(BaseModel):
    info_id: int
    user_id: int
    bank_name: Optional[str] = None
    join_date: Optional[date] = None
    payment_count: Optional[int] = None
    total_payment_amount: Optional[int] = Field(
        None, description="총 납입 인정 금액 (원 단위)"
    )
    is_household_head: Optional[bool] = None
    income_level_percent: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionInfoPayload(BaseModel):
    bank_name: Optional[str] = Field(None, max_length=100)
    join_date: Optional[date] = None
    payment_count: Optional[int] = None
    total_payment_amount: Optional[int] = None
    is_household_head: Optional[bool] = None
    income_level_percent: Optional[int] = None


