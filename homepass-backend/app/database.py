from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 데이터베이스 엔진 생성 (AWS RDS MySQL)
# DATABASE_URL 형식: mysql+pymysql://username:password@host:port/database
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사 (AWS RDS 연결 유지에 중요)
    pool_recycle=3600,   # 1시간마다 연결 재생성
    pool_size=10,        # 연결 풀 크기
    max_overflow=20,     # 최대 추가 연결 수
    echo=False  # SQL 쿼리 로깅 (개발 시 True로 변경 가능)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모델이 상속받을 클래스)
Base = declarative_base()

def get_db():
    """
    데이터베이스 세션 의존성 함수
    FastAPI의 Depends()와 함께 사용
    
    사용 예시:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    데이터베이스 테이블 초기화
    프로덕션에서는 Alembic 마이그레이션 사용 권장
    """
    # 모든 모델 import
    from app import models  # noqa

    Base.metadata.create_all(bind=engine)

    _seed_test_user()
    _seed_announcements()
    _seed_applications()
    _seed_notifications()


def _seed_test_user():
    """기본 테스트 계정을 생성합니다."""
    from sqlalchemy import select
    from app.models import (
        AutoApplyMode,
        NotificationSetting,
        Preference,
        SubscriptionInfo,
        User,
    )

    db = SessionLocal()
    try:
        stmt = select(User).where(User.email == "testuser@example.com")
        user = db.scalars(stmt).first()
        if user:
            return

        user = User(
            email="testuser@example.com",
            password_hash="TestPass123!",
            name="테스트 사용자",
            phone_number="01012345678",
            address="서울특별시 중구 세종대로 110",
        )
        db.add(user)
        db.flush()

        subscription = SubscriptionInfo(
            user_id=user.user_id,
            bank_name="KB국민은행",
            payment_count=12,
            total_payment_amount=2_400_000,
            is_household_head=True,
        )
        db.add(subscription)

        preference = Preference(
            user_id=user.user_id,
            locations=["서울특별시 강남구", "경기도 성남시"],
            housing_types=["행복주택", "공공임대"],
            min_area=33.0,
            max_area=84.0,
            max_deposit=100_000_000,
            max_monthly_rent=50,
            commute_base_address="서울특별시 강남구 삼성동",
            max_commute_time_minutes=60,
            auto_apply_mode=AutoApplyMode.approval,
        )
        db.add(preference)

        notifications = NotificationSetting(
            user_id=user.user_id,
            new_announcement=True,
            auto_apply_complete=True,
            dday=True,
            result=True,
        )
        db.add(notifications)

        db.commit()
    finally:
        db.close()


def _seed_announcements():
    """공고 Mock 데이터를 생성합니다."""
    import json
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from app.models import Announcement

    db = SessionLocal()
    try:
        if db.scalars(select(Announcement)).first():
            return

        now = datetime.now(timezone.utc)
        sample_data = [
            {
                "title": "서울 강남구 행복주택 입주자 모집",
                "source_organization": "서울주택도시공사",
                "source_url": "https://example.com/announcements/gangnam-happy",
                "housing_type": "행복주택",
                "region": "서울특별시 강남구",
                "address_detail": "서울특별시 강남구 테헤란로 123",
                "latitude": 37.499999,
                "longitude": 127.036540,
                "application_end_date": now + timedelta(days=5),
                "original_pdf_url": "https://example.com/files/gangnam-happy.pdf",
                "parsed_content": {
                    "min_deposit": 5000,
                    "max_deposit": 8000,
                    "monthly_rent": 30,
                    "total_households": 150,
                    "eligibility": "소득 하위 80% 이하",
                    "commute_base_address": "서울특별시 강남구 삼성동",
                    "commute_time": 25,
                    "is_customized": True,
                    "image_urls": [
                        "https://homepass-mock.s3.amazonaws.com/announcements/gangnam-happy-01.jpg",
                        "https://homepass-mock.s3.amazonaws.com/announcements/gangnam-happy-02.jpg",
                    ],
                    "schedules": [
                        {"date": (now + timedelta(days=2)).strftime("%Y-%m-%d"), "event": "서류 제출 마감"},
                        {"date": (now + timedelta(days=5)).strftime("%Y-%m-%d"), "event": "신청 마감"},
                        {"date": (now + timedelta(days=12)).strftime("%Y-%m-%d"), "event": "당첨 발표"},
                    ],
                },
            },
            {
                "title": "경기도 성남시 국민임대주택 입주자 모집",
                "source_organization": "경기도시공사",
                "source_url": "https://example.com/announcements/seongnam-national",
                "housing_type": "국민임대",
                "region": "경기도 성남시",
                "address_detail": "경기도 성남시 분당구 성남대로 415",
                "latitude": 37.378979,
                "longitude": 127.112911,
                "application_end_date": now + timedelta(days=12),
                "original_pdf_url": "https://example.com/files/seongnam-national.pdf",
                "parsed_content": {
                    "min_deposit": 3200,
                    "max_deposit": 5200,
                    "monthly_rent": 22,
                    "total_households": 220,
                    "eligibility": "무주택 세대 구성원",
                    "commute_base_address": "경기도 성남시 분당구 서현동",
                    "commute_time": 40,
                    "is_customized": False,
                    "image_urls": [
                        "https://homepass-mock.s3.amazonaws.com/announcements/seongnam-national-01.jpg"
                    ],
                    "schedules": [
                        {"date": (now + timedelta(days=4)).strftime("%Y-%m-%d"), "event": "오프라인 접수"},
                        {"date": (now + timedelta(days=12)).strftime("%Y-%m-%d"), "event": "신청 마감"},
                    ],
                },
            },
            {
                "title": "서울 송파구 청년 전용 행복주택 모집",
                "source_organization": "서울주택도시공사",
                "source_url": "https://example.com/announcements/songpa-youth",
                "housing_type": "행복주택",
                "region": "서울특별시 송파구",
                "address_detail": "서울특별시 송파구 올림픽로 300",
                "latitude": 37.515019,
                "longitude": 127.100151,
                "application_end_date": now + timedelta(days=20),
                "original_pdf_url": "https://example.com/files/songpa-youth.pdf",
                "parsed_content": {
                    "min_deposit": 4200,
                    "max_deposit": 7100,
                    "monthly_rent": 28,
                    "total_households": 180,
                    "eligibility": "만 19-39세 청년, 소득 하위 80% 이하",
                    "commute_base_address": "서울특별시 송파구 잠실동",
                    "commute_time": 35,
                    "is_customized": True,
                    "image_urls": [
                        "https://homepass-mock.s3.amazonaws.com/announcements/songpa-youth-01.jpg",
                        "https://homepass-mock.s3.amazonaws.com/announcements/songpa-youth-02.jpg",
                    ],
                    "schedules": [
                        {"date": (now + timedelta(days=10)).strftime("%Y-%m-%d"), "event": "모집 설명회"},
                        {"date": (now + timedelta(days=20)).strftime("%Y-%m-%d"), "event": "신청 마감"},
                        {"date": (now + timedelta(days=30)).strftime("%Y-%m-%d"), "event": "계약 안내"},
                    ],
                },
            },
        ]

        for entry in sample_data:
            announcement = Announcement(
                title=entry["title"],
                source_organization=entry["source_organization"],
                source_url=entry["source_url"],
                housing_type=entry["housing_type"],
                region=entry["region"],
                address_detail=entry["address_detail"],
                latitude=entry["latitude"],
                longitude=entry["longitude"],
                application_end_date=entry["application_end_date"],
                original_pdf_url=entry["original_pdf_url"],
                scraped_at=now,
                parsed_content=json.dumps(entry["parsed_content"], ensure_ascii=False),
            )
            db.add(announcement)

        db.commit()
    finally:
        db.close()


def _seed_applications():
    """신청 내역 Mock 데이터를 생성합니다."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from app.models import Application, Announcement, User

    db = SessionLocal()
    try:
        user = db.scalars(select(User).where(User.email == "testuser@example.com")).first()
        if not user:
            return

        if db.scalars(select(Application).where(Application.user_id == user.user_id)).first():
            return

        announcements = {ann.title: ann for ann in db.scalars(select(Announcement))}
        now = datetime.now(timezone.utc)

        sample_data = [
            {
                "announcement_title": "서울 강남구 행복주택 입주자 모집",
                "status": "applied",
                "applied_at": now - timedelta(days=2),
            },
            {
                "announcement_title": "경기도 성남시 국민임대주택 입주자 모집",
                "status": "document_review",
                "applied_at": now - timedelta(days=5),
            },
            {
                "announcement_title": "서울 송파구 청년 전용 행복주택 모집",
                "status": "won",
                "applied_at": now - timedelta(days=25),
            },
        ]

        for entry in sample_data:
            announcement = announcements.get(entry["announcement_title"])
            if not announcement:
                continue
            application = Application(
                user_id=user.user_id,
                announcement_id=announcement.announcement_id,
                status=entry["status"],
                applied_at=entry["applied_at"],
            )
            db.add(application)

        db.commit()
    finally:
        db.close()


def _seed_notifications():
    """알림 Mock 데이터를 생성합니다."""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from app.models import Announcement, Notification, User

    db = SessionLocal()
    try:
        user = db.scalars(select(User).where(User.email == "testuser@example.com")).first()
        if not user:
            return

        if db.scalars(select(Notification).where(Notification.user_id == user.user_id)).first():
            return

        announcements = {ann.title: ann for ann in db.scalars(select(Announcement))}
        now = datetime.now(timezone.utc)

        sample_data = [
            {
                "announcement_title": "서울 강남구 행복주택 입주자 모집",
                "message": "[new_announcement] 새로운 공고가 등록되었습니다: 서울 강남구 행복주택",
                "is_read": False,
                "created_at": now - timedelta(hours=3),
            },
            {
                "announcement_title": "경기도 성남시 국민임대주택 입주자 모집",
                "message": "[auto_apply_complete] 자동 신청이 완료되었습니다: 경기도 성남시 국민임대",
                "is_read": False,
                "created_at": now - timedelta(days=1, hours=2),
            },
            {
                "announcement_title": "서울 송파구 청년 전용 행복주택 모집",
                "message": "[dday] D-5: 서울 송파구 청년 전용 행복주택 신청 마감이 5일 남았습니다.",
                "is_read": True,
                "created_at": now - timedelta(days=2),
            },
            {
                "announcement_title": "서울 강남구 행복주택 입주자 모집",
                "message": "[result] 신청 결과가 발표되었습니다: 경쟁률 12.3:1",
                "is_read": True,
                "created_at": now - timedelta(days=3),
            },
        ]

        for entry in sample_data:
            announcement = announcements.get(entry["announcement_title"])
            notification = Notification(
                user_id=user.user_id,
                announcement_id=announcement.announcement_id if announcement else None,
                message=entry["message"],
                is_read=entry["is_read"],
                created_at=entry["created_at"],
            )
            db.add(notification)

        db.commit()
    finally:
        db.close()
