# HomePass - 청약 공고 자동 신청 시스템

## 프로젝트 구조

```
.
├── homepass-front/          # Next.js Frontend
├── homepass-backend/        # FastAPI Backend
├── homepass-scraper/        # Scrapy Web Scraper
├── deployment/              # 배포 관련 파일
│   ├── systemd/            # Systemd 서비스 파일
│   ├── nginx/              # Nginx 설정 파일
│   ├── DEPLOYMENT_GUIDE.md # 상세 배포 가이드
│   └── QUICK_START.md      # 빠른 시작 가이드
└── .github/workflows/       # GitHub Actions 워크플로우
```

## 기술 스택

### Frontend
- Next.js 16
- React 19
- TailwindCSS
- Axios
- React Query

### Backend
- FastAPI
- SQLAlchemy
- MySQL (aiomysql)
- PyJWT
- Uvicorn

### Scraper
- Scrapy
- PyMySQL
- Boto3 (AWS S3)

## 로컬 개발 환경 설정

### Frontend
```bash
cd homepass-front
npm install
npm run dev
# http://localhost:3000
```

### Backend
```bash
cd homepass-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Scraper
```bash
cd homepass-scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
scrapy crawl soco_list_spider
```

## 배포

### 자동 배포 (GitHub Actions)
`main` 또는 `master` 브랜치에 푸시하면 자동으로 배포됩니다.

```bash
git add .
git commit -m "Update: ..."
git push
```

### 수동 배포
상세한 배포 가이드는 다음 문서를 참조하세요:
- **빠른 시작**: [deployment/QUICK_START.md](deployment/QUICK_START.md)
- **상세 가이드**: [deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)

## EC2 정보

- **Host**: ec2-54-191-31-239.us-west-2.compute.amazonaws.com
- **User**: ec2-user
- **Region**: us-west-2

## 포트 구성

- **Frontend**: 3000 (내부), 80 (Nginx proxy)
- **Backend**: 8000 (내부), /api (Nginx proxy)
- **Nginx**: 80 (외부)

## 환경 변수

각 서비스별로 환경 변수 파일이 필요합니다:

### homepass-backend/.env
```env
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/homepass
JWT_SECRET=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```

### homepass-front/.env.local
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### homepass-scraper/.env
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=homepass
```

## API 문서

배포 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://your-ec2-domain/docs
- ReDoc: http://your-ec2-domain/redoc

## 라이선스

이 프로젝트는 Inha University Capstone Project입니다.

## 기여자

- [Your Team Members]

## 문의

문제가 발생하면 이슈를 등록해주세요.
