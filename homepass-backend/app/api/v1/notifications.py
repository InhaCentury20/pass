from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification, User
from app.dependencies.auth import get_current_user
from app.schemas import NotificationItemSchema, NotificationListResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _get_primary_user(db: Session) -> User:
    stmt = select(User).order_by(User.user_id.asc())
    user = db.scalars(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자 계정을 찾을 수 없습니다.")
    return user


def _parse_category(message: str | None) -> tuple[str, str]:
    if not message:
        return "general", ""
    if message.startswith("[") and "]" in message:
        end_idx = message.find("]")
        category = message[1:end_idx]
        content = message[end_idx + 1 :].lstrip()
        return category, content
    return "general", message


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    user = current_user

    stmt = (
        select(Notification)
        .where(Notification.user_id == user.user_id)
        .order_by(Notification.created_at.desc())
    )
    notifications = list(db.scalars(stmt))

    unread_count = sum(1 for notification in notifications if not notification.is_read)
    items: list[NotificationItemSchema] = []

    for notification in notifications:
        category, content = _parse_category(notification.message)
        announcement = notification.announcement
        image_url = None
        announcement_title = None
        if announcement:
            image_urls = announcement.image_urls
            image_url = image_urls[0] if image_urls else None
            announcement_title = announcement.title

        items.append(
            NotificationItemSchema(
                notification_id=notification.notification_id,
                announcement_id=notification.announcement_id,
                category=category,
                message=content or (notification.message or ""),
                is_read=notification.is_read,
                created_at=notification.created_at,
                announcement_title=announcement_title,
                image_url=image_url,
            )
        )

    return NotificationListResponse(total=len(items), unread_count=unread_count, items=items)


class NotificationReadPayload(BaseModel):
    ids: list[int] | None = None


@router.post("/read", response_model=NotificationListResponse)
def mark_notification_as_read(
    payload: NotificationReadPayload | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    user = current_user
    if payload and payload.ids:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user.user_id,
                Notification.notification_id.in_(payload.ids),
            )
            .values(is_read=True)
        )
        db.execute(stmt)
    else:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user.user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        db.execute(stmt)
    db.commit()
    return get_notifications(db, current_user)


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_one_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = current_user
    # 본인 소유 확인 및 업데이트
    notif = db.get(Notification, notification_id)
    if not notif or notif.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    if not notif.is_read:
        notif.is_read = True
        db.add(notif)
        db.commit()
    return {"message": "ok"}
