from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Announcement
from app.schemas import (
    AnnouncementDetailSchema,
    AnnouncementListResponse,
    AnnouncementSchema,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _calculate_dday(end_at: datetime | None) -> int | None:
    if not end_at:
        return None
    days = (end_at.date() - _now().date()).days
    return days if days >= 0 else None


def _serialize_announcement(announcement: Announcement) -> AnnouncementSchema:
    dday = _calculate_dday(announcement.application_end_date)
    return AnnouncementSchema(
        announcement_id=announcement.announcement_id,
        title=announcement.title,
        housing_type=announcement.housing_type,
        region=announcement.region,
        address_detail=announcement.address_detail,
        source_organization=announcement.source_organization,
        source_url=announcement.source_url,
        original_pdf_url=announcement.original_pdf_url,
        latitude=float(announcement.latitude) if announcement.latitude is not None else None,
        longitude=float(announcement.longitude) if announcement.longitude is not None else None,
        application_end_date=announcement.application_end_date,
        scraped_at=announcement.scraped_at,
        post_date=announcement.scraped_at or announcement.application_end_date,
        min_deposit=announcement.min_deposit,
        max_deposit=announcement.max_deposit,
        monthly_rent=announcement.monthly_rent,
        total_households=announcement.total_households,
        eligibility=announcement.eligibility,
        commute_base_address=announcement.commute_base_address,
        commute_time=announcement.commute_time,
        image_urls=announcement.image_urls,
        is_customized=announcement.is_customized,
        dday=dday,
    )


@router.get("", response_model=AnnouncementListResponse)
def get_announcements(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    region: str | None = Query(None, description="지역 필터 (부분 일치)"),
    housing_type: str | None = Query(None, description="주택 유형 필터 (부분 일치)"),
    exclude_past: bool = Query(False, description="마감 지난 공고 제외 (application_end_date >= now)"),
    within_days: int | None = Query(None, ge=0, description="N일 이내 마감 공고만 (application_end_date <= now + N days)"),
    order_by: str | None = Query(None, description="정렬 기준: post_date|scraped_at|application_end_date|title"),
    order: str = Query("asc", description="정렬 방향: asc|desc"),
    db: Session = Depends(get_db),
) -> AnnouncementListResponse:
    stmt = select(Announcement).order_by(Announcement.application_end_date.asc())
    announcements: List[Announcement] = list(db.scalars(stmt))

    # 상대일 기준 필터링 (기본: 파라미터 제공 시 application_end_date IS NULL 제외)
    if exclude_past or within_days is not None:
        now = _now()
        if exclude_past:
            announcements = [
                ann for ann in announcements
                if ann.application_end_date is not None and ann.application_end_date >= now
            ]
        if within_days is not None:
            bound = now + timedelta(days=within_days)
            announcements = [
                ann for ann in announcements
                if ann.application_end_date is not None and ann.application_end_date <= bound
            ]

    if region:
        region_lower = region.lower()
        announcements = [
            ann for ann in announcements if (ann.region or "").lower().find(region_lower) != -1
        ]

    if housing_type:
        housing_lower = housing_type.lower()
        announcements = [
            ann for ann in announcements if (ann.housing_type or "").lower().find(housing_lower) != -1
        ]

    # 정렬 처리 (server-side)
    if order_by:
        order_lower = (order or "asc").lower()
        desc = order_lower == "desc"

        def dt_effective(value: datetime | None) -> datetime:
            if value is None:
                # None을 항상 마지막으로: asc면 최대, desc면 최소로 치환
                return datetime.max if not desc else datetime.min
            return value

        def key_func(ann: Announcement):
            if order_by == "post_date":
                return dt_effective(ann.scraped_at or ann.application_end_date)
            if order_by == "scraped_at":
                return dt_effective(ann.scraped_at)
            if order_by == "application_end_date":
                return dt_effective(ann.application_end_date)
            if order_by == "title":
                return (ann.title or "").lower()
            # 기본: id
            return ann.announcement_id

        announcements.sort(key=key_func, reverse=desc)

    total = len(announcements)
    start = (page - 1) * size
    end = start + size
    sliced = announcements[start:end]

    items = [_serialize_announcement(ann) for ann in sliced]
    return AnnouncementListResponse(total=total, page=page, size=size, items=items)


@router.get("/{announcement_id}", response_model=AnnouncementDetailSchema)
def get_announcement_detail(
    announcement_id: int,
    db: Session = Depends(get_db),
) -> AnnouncementDetailSchema:
    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다.")

    base = _serialize_announcement(announcement).model_dump()
    base["schedules"] = announcement.schedules
    return AnnouncementDetailSchema(**base)
