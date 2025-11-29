from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies.auth import create_session_token
from app.models import User
from app.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    user = db.scalars(select(User).where(User.email == payload.email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # 개발 데이터 호환: 저장된 값이 해시 포맷이 아니면 평문 비교
    ok = False
    if "$" in (user.password_hash or ""):
        ok = verify_password(payload.password, user.password_hash)
    else:
        ok = (payload.password == user.password_hash)

    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    token = create_session_token(user.user_id)
    cookie_params = {
        "key": "session",
        "value": token,
        "httponly": True,
        "samesite": "none",
        "secure": settings.COOKIE_SECURE,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        cookie_params["domain"] = settings.COOKIE_DOMAIN  # type: ignore[index]
    response.set_cookie(**cookie_params)  # type: ignore[arg-type]
    return {"message": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="session",
        path="/",
        samesite="none",
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
    )
    return {"message": "ok"}

