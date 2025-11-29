from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_async import get_async_db
from app.models import Announcement, User, UserInterest
from app.dependencies.auth import get_current_user
from app.schemas.bookmark import BookmarkItem, BookmarkListResponse, BookmarkToggleResponse

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("/{announcement_id}", response_model=BookmarkToggleResponse)
async def toggle_bookmark(
    announcement_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> BookmarkToggleResponse:
    user = current_user

    # 공고 존재 확인
    res_ann = await db.execute(select(Announcement).where(Announcement.announcement_id == announcement_id))
    if not res_ann.scalars().first():
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다.")

    # 기존 북마크 확인
    stmt_existing: Select = select(UserInterest).where(
        and_(
            UserInterest.user_id == user.user_id,
            UserInterest.announcement_id == announcement_id,
        )
    )
    res = await db.execute(stmt_existing)
    existing = res.scalars().first()

    if existing:
        await db.delete(existing)
        await db.commit()
        return BookmarkToggleResponse(is_bookmarked=False)

    new_interest = UserInterest(user_id=user.user_id, announcement_id=announcement_id)
    db.add(new_interest)
    await db.commit()
    return BookmarkToggleResponse(is_bookmarked=True)


@router.get("/me", response_model=BookmarkListResponse)
async def get_my_bookmarks(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
) -> BookmarkListResponse:
    user = current_user
    page = max(page, 1)
    size = max(1, min(size, 100))

    # total
    total_stmt = (
        select(func.count())
        .select_from(UserInterest)
        .where(UserInterest.user_id == user.user_id)
    )
    total = (await db.execute(total_stmt)).scalar_one()

    # page data (join Announcements)
    stmt = (
        select(Announcement)
        .join(UserInterest, UserInterest.announcement_id == Announcement.announcement_id)
        .where(UserInterest.user_id == user.user_id)
        # MySQL은 NULLS LAST를 지원하지 않으므로 IS NULL 정렬 + 컬럼 정렬로 대체
        .order_by(
            func.isnull(Announcement.application_end_date).asc(),
            Announcement.application_end_date.asc(),
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    items: list[BookmarkItem] = []
    for ann in rows:
        image_url = None
        urls = ann.image_urls
        if urls:
            image_url = urls[0]
        items.append(
            BookmarkItem(
                announcement_id=ann.announcement_id,
                title=ann.title,
                housing_type=ann.housing_type,
                region=ann.region,
                image_url=image_url,
                application_end_date=ann.application_end_date,
            )
        )

    return BookmarkListResponse(total=total, page=page, size=size, items=items)

