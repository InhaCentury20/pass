from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PersonalInfoUpdatePayload(BaseModel):
    email: Optional[EmailStr] = Field(
        None, description="이메일 변경 (선택, 미입력시 기존 유지)"
    )
    password: Optional[str] = Field(
        None, description="비밀번호 변경 (선택)"
    )
    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="사용자 이름 (선택)"
    )
    phone_number: Optional[str] = Field(
        None, max_length=20, description="전화번호(선택)"
    )
    address: Optional[str] = Field(
        None, max_length=255, description="주소(선택, 도로명/지번 등)"
    )


class UserSchema(BaseModel):
    user_id: int
    email: EmailStr
    name: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PersonalInfoResponse(BaseModel):
    message: str
    data: UserSchema


class UserProfileResponse(BaseModel):
    message: str
    user: UserSchema
    subscription: Optional["SubscriptionInfoSchema"] = None
    preference: Optional["PreferenceSchema"] = None
    notification: Optional["NotificationSettingSchema"] = None


from app.schemas.subscription import SubscriptionInfoSchema  # noqa: E402
from app.schemas.preference import PreferenceSchema  # noqa: E402
from app.schemas.notification import NotificationSettingSchema  # noqa: E402

