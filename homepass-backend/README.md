# HomePass Backend

청약 공고 자동 신청 시스템의 백엔드 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI 0.120+
- **Language**: Python 3.12+
- **Database**: MySQL (AWS RDS)
- **ORM**: SQLAlchemy 2.0

## 프로젝트 구조

```
back/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 앱 진입점
│   ├── config.py              # 설정 관리 (Pydantic Settings)
│   ├── database.py            # DB 연결 및 세션 관리
│   │
│   ├── api/                   # API 라우터
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── users.py       # 사용자 관련 API
│   │       ├── announcements.py
│   │       ├── applications.py
│   │       ├── notifications.py
│   │       ├── chatbot.py
│   │       └── places.py      # 주변 시설 API (네이버맵 연동)
│   │
│   ├── models/                # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subscription_info.py
│   │   ├── preference.py
│   │   ├── announcement.py
│   │   ├── application.py
│   │   └── notification.py
│   │
│   ├── schemas/               # Pydantic 스키마 (요청/응답)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── ...
│   │
│   ├── services/              # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── announcement_service.py
│   │   └── ...
│   │
│   └── utils/                 # 유틸리티 함수
│       ├── __init__.py
│       └── ...
│
├── scripts/                   # 스크립트 (스크래퍼 등)
├── tests/                     # 테스트 코드
├── venv/                      # Python 가상환경
├── .env                       # 환경 변수
├── .gitignore
├── requirements.txt           # Python 패키지 의존성
└── README.md
```

## 시작하기

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성 (이미 있다면 생략)
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# AWS RDS MySQL 설정
# 형식: mysql+pymysql://username:password@host:port/database
# 예시 (AWS RDS):
DATABASE_URL=mysql+pymysql://admin:password@homepass-db.xxxxx.ap-northeast-2.rds.amazonaws.com:3306/homepass

# 로컬 개발 시:
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/homepass

# CORS 설정 (콤마로 구분)
CORS_ORIGINS=http://localhost:3000

# 네이버 클라우드 플랫폼 (주변 시설 검색용)
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

### 4. 데이터베이스 설정

**AWS RDS MySQL** 또는 로컬 MySQL 데이터베이스를 생성하고 `.env`의 `DATABASE_URL`을 업데이트하세요.

**AWS RDS 설정 예시:**
1. AWS 콘솔에서 RDS MySQL 인스턴스 생성
2. 보안 그룹 설정 (EC2에서 접근 가능하도록)
3. `DATABASE_URL`에 엔드포인트 주소 입력

### 5. 개발 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서는 [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) 또는 [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)에서 확인할 수 있습니다.

## API 엔드포인트

### 사용자 관리
- `GET /api/v1/users/me` - 현재 사용자 정보 조회
- `PUT /api/v1/users/me/subscription-info` - 청약 정보 수정
- `GET /api/v1/users/me/preferences` - 희망 조건 조회
- `PUT /api/v1/users/me/preferences` - 희망 조건 수정

### 공고 관리
- `GET /api/v1/announcements` - 공고 목록 조회 (필터링/정렬 지원)
- `GET /api/v1/announcements/{id}` - 공고 상세 정보 조회

### 신청 관리
- `GET /api/v1/applications` - 신청 내역 조회
- `GET /api/v1/applications/{id}` - 신청 내역 상세 조회
- `POST /api/v1/applications` - 청약 신청 요청

### 알림 관리
- `GET /api/v1/notifications` - 알림 목록 조회
- `POST /api/v1/notifications/read` - 알림 읽음 처리
- `PUT /api/v1/users/me/notification-settings` - 알림 설정 변경

### 기타
- `GET /api/v1/places/nearby` - 주변 시설 조회 (네이버맵 API)
- `POST /api/v1/chatbot/query` - AI 챗봇 질문

자세한 API 명세는 Swagger UI (`/docs`)에서 확인하세요.

## 데이터베이스 모델

주요 엔티티:
- `Users` - 사용자 기본 정보
- `SubscriptionInfo` - 청약 통장 정보
- `Preferences` - 희망 조건
- `Announcements` - 청약 공고
- `Applications` - 신청 내역
- `Notifications` - 알림

자세한 ERD는 프로젝트 루트의 설계서를 참고하세요.

## 네트워크 및 접근 제어

- CORS 설정으로 허용된 Origin만 접근 가능
- AWS RDS는 보안 그룹을 통해 접근 제어

## 테스트

```bash
# 테스트 실행 (구현 예정)
pytest tests/
```

## 배포

### AWS EC2 배포 (예정)

1. EC2 인스턴스에 프로젝트 클론
2. 가상환경 설정 및 의존성 설치
3. `.env` 파일 설정
4. Uvicorn으로 프로세스 실행 (또는 systemd 서비스로 등록)

### Docker 배포 (예정)

```bash
docker build -t homepass-backend .
docker run -p 8000:8000 homepass-backend
```

## 개발 가이드

### 새로운 API 엔드포인트 추가하기

1. `app/api/v1/` 에 새 라우터 파일 생성
2. `app/schemas/` 에 요청/응답 스키마 정의
3. `app/services/` 에 비즈니스 로직 구현
4. `app/main.py` 에 라우터 등록

### 데이터베이스 마이그레이션

SQLAlchemy Alembic을 사용한 마이그레이션 관리 (구현 예정)

```bash
alembic init alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 라이센스

이 프로젝트는 교육용 프로젝트입니다.

