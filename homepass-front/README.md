# HomePass Frontend

청약 공고 자동 신청 시스템의 프론트엔드 애플리케이션입니다.

## 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **State Management**: React Query (@tanstack/react-query)
- **HTTP Client**: Axios

## 프로젝트 구조

```
front/
├── src/
│   ├── app/                    # App Router 페이지
│   │   ├── (auth)/             # 인증 관련 (로그인, 회원가입)
│   │   ├── announcements/      # 공고 목록/상세
│   │   ├── applications/       # 신청 내역
│   │   ├── notifications/      # 알림 내역
│   │   ├── settings/           # 마이페이지/설정
│   │   └── layout.tsx          # 루트 레이아웃
│   ├── components/             # 재사용 컴포넌트
│   │   ├── common/             # 공통 UI (Button, Card 등)
│   │   ├── announcements/     # 공고 관련 컴포넌트
│   │   ├── map/                # 네이버맵 컴포넌트
│   │   └── chatbot/            # AI 챗봇 컴포넌트
│   ├── lib/                    # 유틸리티 함수
│   │   ├── api/                # API 클라이언트
│   │   └── utils/              # 헬퍼 함수
│   ├── types/                  # TypeScript 타입 정의
│   └── hooks/                  # Custom React Hooks
├── public/                     # 정적 파일 (이미지, 폰트 등)
├── .env.local                  # 환경 변수 (로컬 개발용)
└── package.json
```

## 시작하기

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

`.env.local` 파일을 생성하고 다음 내용을 추가하세요:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=your_client_id
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 사용 가능한 스크립트

- `npm run dev` - 개발 서버 실행 (Hot Reload 지원)
- `npm run build` - 프로덕션 빌드 생성
- `npm run start` - 프로덕션 서버 실행
- `npm run lint` - ESLint로 코드 검사

## 주요 기능

### 1. 공고 탐색
- 공고 목록 조회 및 필터링
- 공고 상세 정보 표시
- 지도 기반 위치 정보 제공

### 2. 자동 신청
- 완전 자동 신청 모드
- 알림 후 승인 모드
- 신청 상태 추적

### 3. 알림 관리
- 신규 공고 알림
- 신청 결과 알림
- D-day 알림

### 4. AI 챗봇
- RAG 기반 Q&A
- 청약 용어 설명
- 절차 안내

### 5. 사용자 설정
- 개인 정보 관리
- 청약 정보 관리
- 희망 조건 설정
- 알림 설정

## API 연동

백엔드 API는 `src/lib/api/` 디렉토리에서 관리됩니다.

### API 클라이언트 사용 예시

```typescript
import { apiClient } from '@/lib/api/client';

// 공고 목록 조회
const announcements = await apiClient.get('/api/v1/announcements');

// 사용자 정보 조회
const userInfo = await apiClient.get('/api/v1/users/me');
```

## 스타일 가이드

- 컴포넌트는 함수형 컴포넌트와 TypeScript를 사용합니다
- Tailwind CSS를 사용하여 스타일을 작성합니다
- 반응형 디자인을 고려합니다

## 배포

프로덕션 빌드:

```bash
npm run build
npm run start
```

Vercel에 배포하는 것을 권장합니다. 자세한 내용은 [Next.js 배포 문서](https://nextjs.org/docs/app/building-your-application/deploying)를 참고하세요.
