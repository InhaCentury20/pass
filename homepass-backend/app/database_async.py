from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


def _to_async_mysql_url(url: str) -> str:
    # mysql+pymysql:// -> mysql+aiomysql:// 로 변환
    if url.startswith("mysql+pymysql://"):
        return "mysql+aiomysql://" + url.split("mysql+pymysql://", 1)[1]
    # 이미 async 드라이버거나 다른 DB면 그대로 사용
    return url


ASYNC_DATABASE_URL = _to_async_mysql_url(settings.DATABASE_URL)

_async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    bind=_async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

