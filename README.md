# HomePass · 청약패스

> **흩어진 청약 정보를 하나로, 원클릭 자동 신청 솔루션**
> 분석부터 당첨까지 책임지는 올인원 청약 비서 — *"Save Time, Grab Chance."*
> Inha University Capstone Project · Team **세기말20**

<img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white"/>
<img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white"/>
<img src="https://img.shields.io/badge/Scrapy-60A839?style=for-the-badge&logo=scrapy&logoColor=white"/>
<img src="https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white"/>
<img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white"/>

---

## 📌 프로젝트 소개

청약 정보는 여러 기관·플랫폼에 흩어져 있고, 사이트마다 형식이 달라 비교가 어렵습니다. 핵심 정보는 장황한 PDF 공고문 속에 묻혀 있어 "나에게 맞는 공고인지" 파악하기도 쉽지 않습니다.

**HomePass**는 흩어진 청약 공고를 자동으로 수집·정형화하고, AI로 경쟁률을 예측하며, 신청까지 원클릭으로 자동화하는 **올인원 청약 비서**입니다.

**해결하려는 문제**
- **분산화** — 여러 플랫폼에 정보가 흩어져 있고 통합 검색이 없으며, 실시간 업데이트를 놓치기 쉬움
- **비표준화** — 사이트마다 다른 형식, 표준화되지 않은 데이터 구조로 비교 분석이 어려움
- **숨겨진 정보** — PDF 공고문에 핵심 정보가 묻혀 있고, 장황해서 이해하기 어려움

## ✨ 주요 기능

**1. 데이터 통합 · 정형화**
- Scrapy 기반 크롤링으로 여러 사이트의 공고를 안정적으로 수집, 신규 공고 실시간 반영
- 정규식 + LLM으로 PDF 공고문에서 보증금·월세 등 핵심 정보를 추출해 **표준화된 형태로 제공**

**2. AI 기반 경쟁률 예측**
- 과거 청약 데이터를 학습한 머신러닝 모델로 예상 경쟁률을 **미달 / 보통 / 인기**로 구분 제시
- *(예측 경쟁률은 참고용이며 실제 결과와 다를 수 있음)*

**3. 입지·생활 정보 시각화**
- 네이버 지도 API 연동으로 주소 기반 위치 자동 매핑
- 사용자 직장 위치 기반 **출퇴근 소요 시간** 계산, 반경 내 편의점·마트·병원·학교·공원 등 생활 시설 표시

**4. 원클릭 자동 신청**
- **Playwright + LLM**으로 네이버 폼 자동 제출, 반복 작업 제거로 신청 효율 향상

**5. 개인 맞춤형 공고 & 신청 관리**
- 희망 지역·주택 유형·보증금·면적 등 조건 설정 → 맞춤 공고 필터링 및 관심 공고 지정
- 신청 현황 관리 (신청 완료 / 서류 심사 / 당첨 / 미당첨)

## 🧩 시스템 구조

```
사용자 ── homepass-front (Next.js) ── homepass-backend (FastAPI) ── MySQL
                                              │
                       ┌──────────────────────┼───────────────────────┐
                  homepass-scraper        AI/ML 경쟁률 예측        네이버 지도 API
                  (Scrapy + S3)           · LLM 공고 정형화         · 입지/출퇴근 분석
                                          Playwright 자동 신청
```

## 🛠️ 기술 스택

| 영역 | 스택 |
|------|------|
| **Frontend** | Next.js 16, React 19, TailwindCSS, Axios, React Query |
| **Backend** | FastAPI, SQLAlchemy, MySQL (aiomysql), PyJWT, Uvicorn |
| **Scraper / 자동화** | Scrapy, Playwright, PyMySQL, Boto3 (AWS S3) |
| **AI / Data** | 정규식 + LLM 기반 공고 정형화, 머신러닝 경쟁률 예측 |
| **Infra** | AWS EC2, Nginx, systemd, GitHub Actions (CI/CD) |
| **External API** | 네이버 지도 API |

## 📁 프로젝트 구조

```
.
├── homepass-front/      # Next.js Frontend
├── homepass-backend/    # FastAPI Backend
├── homepass-scraper/    # Scrapy Web Scraper (+ 자동 신청)
├── deployment/          # 배포 (systemd, nginx, 가이드)
└── .github/workflows/   # GitHub Actions CI/CD
```

## 🚀 로컬 개발 환경

```bash
# Frontend
cd homepass-front && npm install && npm run dev          # http://localhost:3000

# Backend
cd homepass-backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload                            # http://localhost:8000 (docs: /docs)

# Scraper
cd homepass-scraper && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
scrapy crawl soco_list_spider
```

## ⚙️ 배포

`main` 브랜치에 push하면 GitHub Actions로 자동 배포됩니다. 상세 절차는 [deployment/QUICK_START.md](deployment/QUICK_START.md)와 [deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)를 참고하세요.

배포 구성: Frontend(3000) · Backend(8000) → Nginx(80) reverse proxy.

## 🔑 환경 변수

각 서비스 디렉토리에 `.env` 파일이 필요합니다.

```ini
# homepass-backend/.env
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/homepass
JWT_SECRET=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]

# homepass-front/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# homepass-scraper/.env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=homepass
```

## 👥 팀 — 세기말20

> 세기말 출생(99·00) 20학번들의 팀

| 이름 | 역할 | 담당 |
|------|------|------|
| 김성윤 | AI | 공고문 요약, 경쟁률 예측 모델 |
| **김용진** | **Full-Stack** | **Scrapy 크롤러 · Playwright 자동 신청 구축** |
| 민동일 | Infra | AWS 서버 구축·배포, 지도 정보 연동 |

## 📈 기대 효과

- **시간 절약** — 통합 정보 제공·PDF 해석·원클릭 신청으로 검색·입력 시간 단축
- **전략적 청약 지원** — 경쟁률 예측 기반 당첨 가능성 높은 공고 추천
- **정보 접근성 향상** — 정보 비대칭 해소, 청년층 주거 안정 지원

---

*Inha University Capstone Project · Team 세기말20*
