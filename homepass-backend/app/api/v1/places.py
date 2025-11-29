from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/places", tags=["places"])

@router.get("/nearby")
def get_nearby_places(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    category: str = Query(..., description="시설 분류 (subway, school, store 등)"),
    db: Session = Depends(get_db)
):
    """
    주변 시설 조회 (네이버맵 API 연동)
    
    - lat, lng: 공고 위치 좌표
    - category: 시설 분류
      - 'subway': 지하철역
      - 'school': 학교
      - 'store': 편의점/마트
    
    TODO: 네이버 지역 검색 API 연동 구현
    """
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="네이버 API 설정이 필요합니다. .env 파일을 확인하세요."
        )
    
    # TODO: 네이버 지역 검색 API 호출 로직 구현
    return {
        "message": "주변 시설 조회 API (구현 예정)",
        "params": {
            "lat": lat,
            "lng": lng,
            "category": category
        }
    }

