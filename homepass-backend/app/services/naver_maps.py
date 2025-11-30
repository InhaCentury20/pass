"""
네이버 클라우드 플랫폼 Maps API 서비스

사용 가능한 API:
- Geocoding: 주소 → 좌표 변환
- Reverse Geocoding: 좌표 → 주소 변환
- Direction 5: 경로 탐색 및 거리/시간 계산
"""

import httpx
from typing import Optional, List, Dict, Any
from app.config import settings


class NaverMapsService:
    """네이버 클라우드 Maps API 클라이언트"""

    BASE_URL = "https://naveropenapi.apigw.ntruss.com"
    SEARCH_BASE_URL = "https://openapi.naver.com/v1"

    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET

        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다.")

    def _get_headers(self) -> Dict[str, str]:
        """네이버 클라우드 Maps API용 헤더"""
        return {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
        }

    def _get_search_headers(self) -> Dict[str, str]:
        """네이버 검색 API용 헤더"""
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """
        주소를 좌표로 변환 (Geocoding)

        Args:
            address: 변환할 주소

        Returns:
            {"lat": float, "lng": float, "address": str} 또는 None
        """
        url = f"{self.BASE_URL}/map-geocode/v2/geocode"
        params = {"query": address}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get("addresses"):
                return None

            first_result = data["addresses"][0]
            return {
                "lat": float(first_result["y"]),
                "lng": float(first_result["x"]),
                "address": first_result.get("roadAddress") or first_result.get("jibunAddress"),
            }

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        좌표를 주소로 변환 (Reverse Geocoding)

        Args:
            lat: 위도
            lng: 경도

        Returns:
            {"address": str, "region": dict} 또는 None
        """
        url = f"{self.BASE_URL}/map-reversegeocode/v2/gc"
        params = {
            "coords": f"{lng},{lat}",
            "orders": "roadaddr,addr",
            "output": "json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()
            results = data.get("results")
            if not results:
                return None

            first_result = results[0]
            region = first_result.get("region", {})
            land = first_result.get("land", {})

            # 도로명 주소 우선, 없으면 지번 주소
            address = None
            if "roadaddr" in first_result:
                address = first_result["roadaddr"].get("roadAddress")
            if not address and "addr" in first_result:
                address = first_result["addr"].get("jibunAddress")

            return {
                "address": address,
                "region": {
                    "area1": region.get("area1", {}).get("name"),  # 시/도
                    "area2": region.get("area2", {}).get("name"),  # 구/군
                    "area3": region.get("area3", {}).get("name"),  # 동/읍/면
                }
            }

    async def get_directions(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        option: str = "trafast"
    ) -> Optional[Dict[str, Any]]:
        """
        두 지점 간 경로 탐색 (Direction 5)

        Args:
            start_lat: 출발지 위도
            start_lng: 출발지 경도
            end_lat: 도착지 위도
            end_lng: 도착지 경도
            option: 경로 옵션 (trafast: 실시간 빠른길, tracomfort: 편안한길, traoptimal: 최적)

        Returns:
            {"distance": int (m), "duration": int (ms), "path": list} 또는 None
        """
        url = f"{self.BASE_URL}/map-direction/v1/driving"
        params = {
            "start": f"{start_lng},{start_lat}",
            "goal": f"{end_lng},{end_lat}",
            "option": option
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10.0
            )

            if response.status_code != 200:
                return None

            data = response.json()
            route = data.get("route", {}).get(option)
            if not route or len(route) == 0:
                return None

            summary = route[0]["summary"]
            path = route[0]["path"]

            return {
                "distance": summary["distance"],  # 미터
                "duration": summary["duration"],  # 밀리초
                "path": [[p[1], p[0]] for p in path],  # [lat, lng] 형식으로 변환
            }

    async def search_local(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 1000,
        display: int = 5
    ) -> List[Dict[str, Any]]:
        """
        주변 시설 검색 (Naver Search API - Local)

        Args:
            query: 검색어 (예: "지하철역", "학교", "편의점")
            lat: 중심 위도
            lng: 중심 경도
            radius: 검색 반경 (미터, 최대 5000)
            display: 결과 개수 (최대 5)

        Returns:
            주변 시설 목록 [{"name": str, "address": str, "distance": str, ...}]
        """
        url = f"{self.SEARCH_BASE_URL}/search/local.json"
        params = {
            "query": query,
            "display": min(display, 5),
            "start": 1,
            "sort": "random"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._get_search_headers(),
                timeout=10.0
            )

            if response.status_code != 200:
                return []

            data = response.json()
            items = data.get("items", [])

            # 결과 가공
            results = []
            for item in items:
                # HTML 태그 제거
                name = item.get("title", "").replace("<b>", "").replace("</b>", "")
                address = item.get("roadAddress") or item.get("address", "")

                results.append({
                    "name": name,
                    "address": address,
                    "category": item.get("category", ""),
                    "telephone": item.get("telephone", ""),
                    "mapx": item.get("mapx", ""),  # 네이버 좌표계 (변환 필요)
                    "mapy": item.get("mapy", ""),
                    "link": item.get("link", ""),
                })

            return results

    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        카테고리별 주변 시설 조회

        Args:
            lat: 중심 위도
            lng: 중심 경도
            category: 시설 분류 (subway, school, store, hospital, park)

        Returns:
            주변 시설 목록
        """
        # 카테고리별 검색 키워드 매핑
        category_keywords = {
            "subway": "지하철역",
            "school": "초등학교",
            "store": "편의점",
            "hospital": "병원",
            "park": "공원",
            "mart": "마트",
        }

        keyword = category_keywords.get(category)
        if not keyword:
            return []

        # 주변 시설 검색
        places = await self.search_local(
            query=keyword,
            lat=lat,
            lng=lng,
            radius=1000,
            display=5
        )

        return places


# 싱글톤 인스턴스
_naver_maps_service: Optional[NaverMapsService] = None


def get_naver_maps_service() -> NaverMapsService:
    """네이버 Maps 서비스 인스턴스 반환"""
    global _naver_maps_service
    if _naver_maps_service is None:
        _naver_maps_service = NaverMapsService()
    return _naver_maps_service
