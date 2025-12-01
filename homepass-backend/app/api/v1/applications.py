from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, User
from app.schemas import (
    ApplicationAnnouncementSummary,
    ApplicationDetailSchema,
    ApplicationItemSchema,
    ApplicationListResponse,
)

router = APIRouter(prefix="/applications", tags=["applications"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _calculate_dday(end_at: datetime | None) -> int | None:
    if not end_at:
        return None
    days = (end_at.date() - _now().date()).days
    return days if days >= 0 else None


def _get_primary_user(db: Session) -> User:
    stmt = select(User).order_by(User.user_id.asc())
    user = db.scalars(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자 계정을 찾을 수 없습니다.")
    return user


def _build_items(applications: list[Application]) -> list[ApplicationItemSchema]:
    items: list[ApplicationItemSchema] = []
    for application in applications:
        announcement = application.announcement
        announcement_title = announcement.title if announcement else "알 수 없는 공고"
        image_url = None
        housing_type = None
        region = None
        dday = None

        if announcement:
            image_urls = announcement.image_urls
            image_url = image_urls[0] if image_urls else None
            housing_type = announcement.housing_type
            region = announcement.region
            dday = _calculate_dday(announcement.application_end_date)

        items.append(
            ApplicationItemSchema(
                application_id=application.application_id,
                announcement_id=application.announcement_id,
                announcement_title=announcement_title,
                status=application.status,
                applied_at=application.applied_at,
                status_updated_at=application.status_updated_at,
                image_url=image_url,
                housing_type=housing_type,
                region=region,
                dday=dday,
            )
        )
    return items


def _build_announcement_summary(announcement) -> ApplicationAnnouncementSummary | None:
    if not announcement:
        return None
    image_urls = announcement.image_urls or []
    return ApplicationAnnouncementSummary(
        announcement_id=announcement.announcement_id,
        title=announcement.title,
        housing_type=announcement.housing_type,
        region=announcement.region,
        application_end_date=announcement.application_end_date,
        source_url=announcement.source_url,
        application_link=announcement.application_link,
        image_urls=image_urls,
        min_deposit=announcement.min_deposit,
        max_deposit=announcement.max_deposit,
        monthly_rent=announcement.monthly_rent,
        eligibility=announcement.eligibility,
    )


@router.get("", response_model=ApplicationListResponse)
def get_applications(db: Session = Depends(get_db)) -> ApplicationListResponse:
    user = _get_primary_user(db)

    stmt = (
        select(Application)
        .where(Application.user_id == user.user_id)
        .order_by(Application.applied_at.desc())
    )
    applications = list(db.scalars(stmt))

    items = _build_items(applications)
    return ApplicationListResponse(total=len(items), items=items)


@router.get("/{application_id}", response_model=ApplicationDetailSchema)
def get_application_detail(application_id: int, db: Session = Depends(get_db)) -> ApplicationDetailSchema:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="신청 내역을 찾을 수 없습니다.")

    item_schema = _build_items([application])[0]
    announcement_summary = _build_announcement_summary(application.announcement)

    return ApplicationDetailSchema(
        **item_schema.model_dump(),
        announcement_detail=announcement_summary,
    )


@router.get("/users/{user_id}", response_model=ApplicationListResponse)
def get_applications_by_user(user_id: int, db: Session = Depends(get_db)) -> ApplicationListResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 계정을 찾을 수 없습니다.")

    stmt = (
        select(Application)
        .where(Application.user_id == user.user_id)
        .order_by(Application.applied_at.desc())
    )
    applications = list(db.scalars(stmt))
    items = _build_items(applications)
    return ApplicationListResponse(total=len(items), items=items)
