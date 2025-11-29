from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.preference import AutoApplyMode


class PreferenceSchema(BaseModel):
    pref_id: int
    user_id: int
    locations: Optional[List[str]] = None
    housing_types: Optional[List[str]] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    max_deposit: Optional[int] = Field(None, description="최대 보증금 (원 단위)")
    max_monthly_rent: Optional[int] = Field(None, description="최대 월 임대료 (만원)")
    commute_base_address: Optional[str] = None
    max_commute_time_minutes: Optional[int] = None
    auto_apply_mode: Optional[AutoApplyMode] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PreferencePayload(BaseModel):
    locations: Optional[List[str]] = None
    housing_types: Optional[List[str]] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    max_deposit: Optional[int] = None
    max_monthly_rent: Optional[int] = None
    commute_base_address: Optional[str] = None
    max_commute_time_minutes: Optional[int] = None
    auto_apply_mode: Optional[AutoApplyMode] = Field(
        None, description="자동 신청 모드 (full_auto, approval, disabled)"
    )


class AutoApplyModePayload(BaseModel):
    auto_apply_mode: AutoApplyMode

