"""주변 시설 관련 스키마"""

from pydantic import BaseModel
from typing import List, Optional


class PlaceSchema(BaseModel):
    """주변 시설 정보"""
    name: str
    address: str
    category: Optional[str] = None
    telephone: Optional[str] = None
    mapx: Optional[str] = None  # 네이버 좌표계 X (경도)
    mapy: Optional[str] = None  # 네이버 좌표계 Y (위도)
    link: Optional[str] = None


class NearbyPlacesResponse(BaseModel):
    """주변 시설 조회 응답"""
    center: dict  # {"lat": float, "lng": float}
    category: str
    places: List[PlaceSchema]


class GeocodeRequest(BaseModel):
    """주소 → 좌표 변환 요청"""
    address: str


class GeocodeResponse(BaseModel):
    """주소 → 좌표 변환 응답"""
    lat: float
    lng: float
    address: str


class ReverseGeocodeResponse(BaseModel):
    """좌표 → 주소 변환 응답"""
    address: Optional[str]
    region: dict


class DirectionsRequest(BaseModel):
    """경로 탐색 요청"""
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    option: str = "trafast"  # trafast, tracomfort, traoptimal


class DirectionsResponse(BaseModel):
    """경로 탐색 응답"""
    distance: int  # 미터
    duration: int  # 밀리초
    path: List[List[float]]  # [[lat, lng], ...]


class CommuteInfoResponse(BaseModel):
    """출퇴근 정보 응답"""
    start_address: str  # 출발지 주소 (공고 주소)
    end_address: str  # 도착지 주소 (유저 주소)
    distance: int  # 거리 (미터)
    duration: int  # 소요 시간 (밀리초)
    duration_minutes: int  # 소요 시간 (분)
    path: List[List[float]]  # 경로 좌표 [[lat, lng], ...]
