from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


PREFERRED_USER_ID = 4


def get_current_user(
    db: Session = Depends(get_db),
) -> User:
    """
    로그인 과정을 제거하고, 항상 지정된 테스트 사용자로 동작하게 합니다.
    우선 user_id=4를 찾고, 없으면 기존 로직으로 대체합니다.
    """
    user: Optional[User] = db.get(User, PREFERRED_USER_ID)
    if not user:
        user = db.scalars(
            select(User).where(User.email == "testuser@example.com")
        ).first()
    if not user:
        user = db.scalars(select(User).order_by(User.user_id.asc())).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자 계정을 찾을 수 없습니다.")
    return user

