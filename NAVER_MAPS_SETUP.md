# 네이버 클라우드 Maps API 통합 가이드

네이버 클라우드 Maps API를 이용한 공고 위치 기반 주변 정보 조회 기능이 통합되었습니다.

## 📋 구현된 기능

### Backend (FastAPI)
1. **Naver Maps 서비스 클라이언트** (`homepass-backend/app/services/naver_maps.py`)
   - Geocoding: 주소 → 좌표 변환
   - Reverse Geocoding: 좌표 → 주소 변환
   - Direction 5: 경로 탐색 및 거리/시간 계산
   - Local Search: 주변 시설 검색 (지하철역, 학교, 편의점, 병원, 공원 등)

2. **Places API 엔드포인트** (`homepass-backend/app/api/v1/places.py`)
   - `GET /api/v1/places/nearby` - 주변 시설 조회
   - `POST /api/v1/places/geocode` - 주소를 좌표로 변환
   - `GET /api/v1/places/reverse-geocode` - 좌표를 주소로 변환
   - `POST /api/v1/places/directions` - 경로 탐색

### Frontend (Next.js)
1. **NaverMap 컴포넌트** (`homepass-front/src/components/common/NaverMap.tsx`)
   - 네이버 Dynamic Map 표시
   - 주택 위치 마커 표시
   - 주변 시설 마커 및 정보창 표시

2. **공고 상세 페이지 통합**
   - 출퇴근/주변 탭에 지도 표시
   - 카테고리별 주변 시설 검색 및 표시
   - 실시간 데이터 로딩

## 🔧 환경 설정

### 1. Backend 환경 변수 설정

`homepass-backend/.env` 파일에 다음 내용이 추가되어 있습니다:

```bash
# --- Naver Cloud (주변 시설 검색용) ---
NAVER_CLIENT_ID=8w5hzhnvg4
NAVER_CLIENT_SECRET=sxUjm3oQYq1MFeugvCCKrTxsIVq1uk1QD1GiIUmN
```

### 2. Frontend 환경 변수 설정

`homepass-front/.env.local` 파일에 다음 내용이 추가되어 있습니다:

```bash
# Naver Maps API
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=8w5hzhnvg4
```

## 🚀 테스트 방법

### 환경 설정

현재 프로젝트는 EC2 서버를 사용하도록 설정되어 있습니다:
- **Backend API**: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com
- **Frontend**: 로컬 개발 환경 (http://localhost:3000)

### 1. Backend (EC2에 배포된 경우)

EC2 서버에 이미 배포되어 있다면, API 문서를 확인할 수 있습니다:
- Swagger UI: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/docs
- ReDoc: http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/redoc

### 2. Frontend 로컬 실행

```bash
# 1. 프론트엔드 디렉토리로 이동
cd homepass-front

# 2. 의존성 설치 (처음 한 번만)
npm install

# 3. 개발 서버 실행
npm run dev
```

프론트엔드가 정상적으로 실행되면:
- 프론트엔드: http://localhost:3000
- Backend API는 EC2 서버의 엔드포인트를 사용

### 로컬에서 Backend도 실행하려면

로컬 개발이 필요한 경우:

```bash
# 1. 백엔드 디렉토리로 이동
cd homepass-backend

# 2. 가상 환경 활성화
source venv/bin/activate

# 3. 의존성 확인
pip install -r requirements.txt

# 4. FastAPI 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

그리고 `homepass-front/.env.local` 파일을 수정:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 기능 테스트

#### 3.1. API 직접 테스트 (Swagger UI 사용)

1. 브라우저에서 http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/docs 접속
2. **places** 태그 확인
3. 테스트할 API 선택:

**주변 시설 조회 테스트:**
```
GET /api/v1/places/nearby
```
파라미터:
- lat: `37.5665` (서울시청 위도)
- lng: `126.9780` (서울시청 경도)
- category: `subway` (지하철역)

"Try it out" → "Execute" 클릭하여 결과 확인

**Geocoding 테스트:**
```
POST /api/v1/places/geocode
```
Request Body:
```json
{
  "address": "서울특별시 중구 세종대로 110"
}
```

#### 3.2. Frontend에서 테스트

1. http://localhost:3000 접속
2. 공고 목록에서 아무 공고나 클릭
3. **출퇴근/주변** 탭 클릭
4. 지도가 표시되는지 확인
5. 주변 시설 카테고리(지하철역, 학교, 편의점 등) 버튼 클릭
6. 지도에 마커가 표시되고, 하단에 시설 목록이 표시되는지 확인

#### 3.3. 터미널에서 curl 테스트

```bash
# EC2 서버 주소
API_URL="http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com"

# 주변 지하철역 검색
curl -X GET "$API_URL/api/v1/places/nearby?lat=37.5665&lng=126.9780&category=subway"

# Geocoding
curl -X POST "$API_URL/api/v1/places/geocode" \
  -H "Content-Type: application/json" \
  -d '{"address": "서울특별시 중구 세종대로 110"}'

# Reverse Geocoding
curl -X GET "$API_URL/api/v1/places/reverse-geocode?lat=37.5665&lng=126.9780"

# 경로 탐색
curl -X POST "$API_URL/api/v1/places/directions" \
  -H "Content-Type: application/json" \
  -d '{
    "start_lat": 37.5665,
    "start_lng": 126.9780,
    "end_lat": 37.5512,
    "end_lng": 126.9882,
    "option": "trafast"
  }'
```

## 🧪 테스트 데이터

공고 데이터에 위도/경도가 없는 경우, 다음과 같이 직접 테스트할 수 있습니다:

### 테스트용 좌표

| 위치 | 위도(lat) | 경도(lng) |
|------|-----------|-----------|
| 서울시청 | 37.5665 | 126.9780 |
| 강남역 | 37.4979 | 127.0276 |
| 여의도 | 37.5219 | 126.9245 |
| 잠실 | 37.5133 | 127.1000 |
| 인천대학교 | 37.3750 | 126.6325 |

### 카테고리 목록

- `subway`: 지하철역 🚇
- `school`: 초등학교 🏫
- `store`: 편의점 🏪
- `hospital`: 병원 🏥
- `park`: 공원 🌳
- `mart`: 마트 🛒

## 🔍 문제 해결

### 1. "네이버 API 설정이 필요합니다" 오류

**원인:** 환경 변수가 제대로 설정되지 않음

**해결:**
1. `homepass-backend/.env` 파일 확인
2. `NAVER_CLIENT_ID`와 `NAVER_CLIENT_SECRET`이 올바르게 설정되었는지 확인
3. 서버 재시작 (uvicorn 프로세스 종료 후 다시 실행)

### 2. 지도가 표시되지 않음

**원인:** 프론트엔드 환경 변수 미설정 또는 잘못된 Client ID

**해결:**
1. `homepass-front/.env.local` 파일 확인
2. `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID`가 설정되었는지 확인
3. Next.js 개발 서버 재시작 (Ctrl+C 후 `npm run dev`)

### 3. "주변 시설을 찾을 수 없습니다" 메시지

**원인:**
- 공고에 위도/경도 데이터가 없음
- 해당 위치 주변에 실제로 시설이 없음
- 네이버 Search API 인증 오류

**해결:**
1. 공고 데이터의 `latitude`, `longitude` 필드 확인
2. 브라우저 개발자 도구 → Network 탭에서 API 응답 확인
3. Backend 로그 확인 (터미널 출력)

### 4. CORS 오류

**원인:** 프론트엔드에서 백엔드 API 호출 시 CORS 정책 문제

**해결:**
1. `homepass-backend/app/config.py` 파일에서 CORS_ORIGINS 확인
2. `http://localhost:3000`이 포함되어 있는지 확인
3. 서버 재시작

## 📝 추가 개선 사항

현재 구현에서 다음과 같은 개선이 가능합니다:

1. **좌표 변환 정확도**
   - 네이버 Search API가 반환하는 좌표(mapx, mapy)는 네이버 자체 좌표계
   - WGS84로 정확한 변환이 필요할 수 있음

2. **더 많은 시설 카테고리**
   - 카페, 음식점, 은행 등 추가 가능

3. **거리 정보 표시**
   - Direction API를 활용하여 주택에서 각 시설까지의 실제 거리/시간 표시

4. **즐겨찾기 기능**
   - 자주 찾는 시설을 저장하는 기능

## 🔗 참고 자료

- [네이버 클라우드 플랫폼 Maps API 문서](https://api.ncloud-docs.com/docs/ai-naver-mapsgeocoding)
- [네이버 검색 API - 지역 검색](https://developers.naver.com/docs/serviceapi/search/local/local.md)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 공식 문서](https://nextjs.org/docs)

## ✅ 체크리스트

다음을 확인하세요:

- [ ] Backend API가 EC2에서 정상 작동 (http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com/docs)
- [ ] Frontend 서버가 http://localhost:3000에서 실행 중
- [ ] Swagger UI에서 places API 확인 가능
- [ ] `/api/v1/places/nearby` API 호출 성공
- [ ] 공고 상세 페이지에서 지도 표시
- [ ] 주변 시설 카테고리 클릭 시 마커 표시
- [ ] 주변 시설 목록 표시

모든 항목이 체크되면 성공적으로 통합이 완료된 것입니다! 🎉

## 📌 중요 참고사항

### EC2 서버 재배포 필요

백엔드 코드가 변경되었으므로, EC2 서버에 새로운 코드를 배포해야 합니다:

1. 변경된 파일들:
   - `homepass-backend/app/services/naver_maps.py` (새 파일)
   - `homepass-backend/app/schemas/place.py` (새 파일)
   - `homepass-backend/app/api/v1/places.py` (수정됨)
   - `homepass-backend/.env` (네이버 API 키 추가)

2. EC2 서버에 배포 후 서버 재시작 필요

3. 환경 변수가 제대로 로드되었는지 확인
