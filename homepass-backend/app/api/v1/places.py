from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.naver_maps import get_naver_maps_service, NaverMapsService
from app.schemas.place import (
    NearbyPlacesResponse,
    GeocodeRequest,
    GeocodeResponse,
    ReverseGeocodeResponse,
    DirectionsRequest,
    DirectionsResponse,
)

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/nearby", response_model=NearbyPlacesResponse)
async def get_nearby_places(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    category: str = Query(..., description="시설 분류 (subway, school, store, hospital, park, mart)"),
    naver_maps: NaverMapsService = Depends(get_naver_maps_service),
):
    """
    주변 시설 조회 (네이버 검색 API 연동)

    - lat, lng: 공고 위치 좌표
    - category: 시설 분류
      - 'subway': 지하철역
      - 'school': 초등학교
      - 'store': 편의점
      - 'hospital': 병원
      - 'park': 공원
      - 'mart': 마트
    """
    try:
        places = await naver_maps.get_nearby_places(lat, lng, category)

        return NearbyPlacesResponse(
            center={"lat": lat, "lng": lng},
            category=category,
            places=places
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주변 시설 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/nearby-by-address", response_model=NearbyPlacesResponse)
async def get_nearby_places_by_address(
    address: str = Query(..., description="주소 (예: 서울시 관악구 신림동)"),
    category: str = Query(..., description="시설 분류 (subway, school, store, hospital, park, mart)"),
    naver_maps: NaverMapsService = Depends(get_naver_maps_service),
):
    """
    주소 기반 주변 시설 조회

    주소를 Geocoding으로 좌표로 변환한 후 주변 시설을 검색합니다.

    - address: 검색할 주소
    - category: 시설 분류
      - 'subway': 지하철역
      - 'school': 초등학교
      - 'store': 편의점
      - 'hospital': 병원
      - 'park': 공원
      - 'mart': 마트
    """
    try:
        # 1. 주소를 좌표로 변환
        geocode_result = await naver_maps.geocode(address)

        if not geocode_result:
            raise HTTPException(
                status_code=404,
                detail=f"주소를 찾을 수 없습니다: {address}"
            )

        lat = geocode_result["lat"]
        lng = geocode_result["lng"]

        # 2. 좌표로 주변 시설 검색
        places = await naver_maps.get_nearby_places(lat, lng, category)

        return NearbyPlacesResponse(
            center={"lat": lat, "lng": lng},
            category=category,
            places=places
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주변 시설 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    naver_maps: NaverMapsService = Depends(get_naver_maps_service),
):
    """
    주소를 좌표로 변환 (Geocoding)

    - address: 변환할 주소 (예: "서울시 강남구 테헤란로 152")
    """
    try:
        result = await naver_maps.geocode(request.address)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="주소를 찾을 수 없습니다."
            )

        return GeocodeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode_location(
    lat: float = Query(..., description="위도"),
    lng: float = Query(..., description="경도"),
    naver_maps: NaverMapsService = Depends(get_naver_maps_service),
):
    """
    좌표를 주소로 변환 (Reverse Geocoding)

    - lat, lng: 변환할 좌표
    """
    try:
        result = await naver_maps.reverse_geocode(lat, lng)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="주소를 찾을 수 없습니다."
            )

        return ReverseGeocodeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reverse Geocoding 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/directions", response_model=DirectionsResponse)
async def get_directions(
    request: DirectionsRequest,
    naver_maps: NaverMapsService = Depends(get_naver_maps_service),
):
    """
    두 지점 간 경로 탐색 (Direction 5)

    - start_lat, start_lng: 출발지 좌표
    - end_lat, end_lng: 도착지 좌표
    - option: 경로 옵션 (trafast: 실시간 빠른길, tracomfort: 편안한길, traoptimal: 최적)
    """
    try:
        result = await naver_maps.get_directions(
            request.start_lat,
            request.start_lng,
            request.end_lat,
            request.end_lng,
            request.option
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="경로를 찾을 수 없습니다."
            )

        return DirectionsResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"경로 탐색 중 오류가 발생했습니다: {str(e)}"
        )

