from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(
    db: Session = Depends(get_db),
) -> User:
    """
    로그인 과정을 제거하고, 항상 테스트 사용자로 동작하게 합니다.
    우선 email='testuser@example.com'을 찾고, 없으면 가장 작은 user_id 사용.
    """
    user: Optional[User] = db.scalars(
        select(User).where(User.email == "testuser@example.com")
    ).first()
    if not user:
        user = db.scalars(select(User).order_by(User.user_id.asc())).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자 계정을 찾을 수 없습니다.")
    return user

