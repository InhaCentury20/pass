from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotificationSetting, Preference, SubscriptionInfo, User
from app.dependencies.auth import get_current_user
from app.schemas import (
    AutoApplyModePayload,
    NotificationSettingPayload,
    NotificationSettingSchema,
    PersonalInfoResponse,
    PersonalInfoUpdatePayload,
    PreferencePayload,
    PreferenceSchema,
    SubscriptionInfoPayload,
    SubscriptionInfoSchema,
    UserProfileResponse,
    UserSchema,
)

router = APIRouter(prefix="/users", tags=["users"])


def _get_primary_user(db: Session) -> User:
    stmt = select(User).order_by(User.user_id.asc())
    user = db.scalars(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자 계정을 찾을 수 없습니다.")
    return user


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    user = db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 계정을 찾을 수 없습니다.")

    subscription = user.subscription_info
    preference = user.preference
    notification = user.notification_setting

    return UserProfileResponse(
        message="사용자 정보를 조회했습니다.",
        user=UserSchema.model_validate(user),
        subscription=(
            SubscriptionInfoSchema.model_validate(subscription)
            if subscription
            else None
        ),
        preference=(
            PreferenceSchema.model_validate(preference) if preference else None
        ),
        notification=(
            NotificationSettingSchema.model_validate(notification)
            if notification
            else None
        ),
    )


@router.put(
    "/me/personal-info",
    response_model=PersonalInfoResponse,
)
def update_personal_info(
    payload: PersonalInfoUpdatePayload,
    db: Session = Depends(get_db),
) -> PersonalInfoResponse:
    user = _get_primary_user(db)

    if payload.email and payload.email != user.email:
        stmt = select(User).where(User.email == payload.email)
        existing = db.scalars(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다.",
            )
        user.email = payload.email

    if payload.password:
        user.password_hash = payload.password
    if payload.name is not None:
        user.name = payload.name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.address is not None:
        user.address = payload.address

    db.add(user)
    db.commit()
    db.refresh(user)

    return PersonalInfoResponse(
        message="사용자 정보를 저장했습니다.",
        data=UserSchema.model_validate(user),
    )


@router.put(
    "/me/subscription-info",
    response_model=SubscriptionInfoSchema,
)
def update_subscription_info(
    payload: SubscriptionInfoPayload,
    db: Session = Depends(get_db),
) -> SubscriptionInfoSchema:
    user = _get_primary_user(db)

    subscription = user.subscription_info
    if not subscription:
        subscription = SubscriptionInfo(user_id=user.user_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return SubscriptionInfoSchema.model_validate(subscription)


@router.put(
    "/me/preferences",
    response_model=PreferenceSchema,
)
def update_preferences(
    payload: PreferencePayload,
    db: Session = Depends(get_db),
) -> PreferenceSchema:
    user = _get_primary_user(db)

    preference = user.preference
    if not preference:
        preference = Preference(user_id=user.user_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(preference, field, value)

    db.add(preference)
    db.commit()
    db.refresh(preference)

    return PreferenceSchema.model_validate(preference)


@router.put(
    "/me/auto-apply-mode",
    response_model=PreferenceSchema,
)
def update_auto_apply_mode(
    payload: AutoApplyModePayload,
    db: Session = Depends(get_db),
) -> PreferenceSchema:
    user = _get_primary_user(db)

    preference = user.preference
    if not preference:
        preference = Preference(user_id=user.user_id)

    preference.auto_apply_mode = payload.auto_apply_mode

    db.add(preference)
    db.commit()
    db.refresh(preference)

    return PreferenceSchema.model_validate(preference)


@router.put(
    "/me/notification-settings",
    response_model=NotificationSettingSchema,
)
def update_notification_settings(
    payload: NotificationSettingPayload,
    db: Session = Depends(get_db),
) -> NotificationSettingSchema:
    user = _get_primary_user(db)

    notification = user.notification_setting
    if not notification:
        notification = NotificationSetting(user_id=user.user_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(notification, field, value)

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return NotificationSettingSchema.model_validate(notification)
