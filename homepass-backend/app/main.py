from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db

app = FastAPI(
    title="HomePass API",
    description="청약 공고 자동 신청 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "HomePass API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# API 라우터 등록
from app.api.v1 import (
    users,
    announcements,
    applications,
    notifications,
    bookmarks,
    chatbot,
    places,
)

# DB 초기화 및 시드
init_db()

app.include_router(users.router, prefix="/api/v1")
app.include_router(announcements.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(bookmarks.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")

