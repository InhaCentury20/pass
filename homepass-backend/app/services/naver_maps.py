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
    """네이버 클라우드 Maps API 및 검색 API 클라이언트"""

    BASE_URL = "https://naveropenapi.apigw.ntruss.com"
    SEARCH_BASE_URL = "https://openapi.naver.com/v1"

    def __init__(self):
        # 네이버 클라우드 Maps API (Geocoding, Direction 등)
        self.cloud_client_id = settings.NAVER_CLOUD_CLIENT_ID
        self.cloud_client_secret = settings.NAVER_CLOUD_CLIENT_SECRET

        # 네이버 검색 API (주변 시설 검색)
        self.search_client_id = settings.NAVER_SEARCH_CLIENT_ID
        self.search_client_secret = settings.NAVER_SEARCH_CLIENT_SECRET

        if not self.cloud_client_id or not self.cloud_client_secret:
            raise ValueError("네이버 클라우드 Maps API 키가 설정되지 않았습니다.")

    def _get_headers(self) -> Dict[str, str]:
        """네이버 클라우드 Maps API용 헤더"""
        return {
            "X-NCP-APIGW-API-KEY-ID": self.cloud_client_id,
            "X-NCP-APIGW-API-KEY": self.cloud_client_secret,
        }

    def _get_search_headers(self) -> Dict[str, str]:
        """네이버 검색 API용 헤더"""
        return {
            "X-Naver-Client-Id": self.search_client_id,
            "X-Naver-Client-Secret": self.search_client_secret,
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

            print(f"[DEBUG] Reverse Geocode URL: {url}")
            print(f"[DEBUG] Params: {params}")
            print(f"[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")

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
        # 1. Reverse Geocoding으로 지역명 추출
        location_info = await self.reverse_geocode(lat, lng)
        region_name = ""
        if location_info and location_info.get("region"):
            region = location_info["region"]
            # 시/도, 구/군, 동 정보를 조합
            region_name = f"{region.get('area1', '')} {region.get('area2', '')} {region.get('area3', '')}".strip()

        # 검색 쿼리에 지역명 추가
        search_query = f"{region_name} {query}".strip() if region_name else query

        url = f"{self.SEARCH_BASE_URL}/search/local.json"
        params = {
            "query": search_query,
            "display": 20,  # 더 많이 가져와서 거리순 필터링
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

            print(f"[DEBUG] Search Local URL: {url}")
            print(f"[DEBUG] Query: {search_query}, Params: {params}")
            print(f"[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text[:500]}")

            if response.status_code != 200:
                print(f"[ERROR] Search API failed with status {response.status_code}")
                raise Exception(f"Search API returned {response.status_code}")

            data = response.json()
            items = data.get("items", [])

            # 결과 가공 및 거리 계산
            results = []
            for item in items:
                mapx = item.get("mapx", "")
                mapy = item.get("mapy", "")

                if not mapx or not mapy:
                    continue

                # 네이버 좌표를 WGS84로 변환 (간단 근사)
                item_lng = float(mapx) / 10000000
                item_lat = float(mapy) / 10000000

                # 거리 계산 (Haversine formula - 단순 근사)
                distance = self._calculate_distance(lat, lng, item_lat, item_lng)

                # 반경 내에 있는 것만 포함
                if distance <= radius:
                    # HTML 태그 제거
                    name = item.get("title", "").replace("<b>", "").replace("</b>", "")
                    address = item.get("roadAddress") or item.get("address", "")

                    results.append({
                        "name": name,
                        "address": address,
                        "category": item.get("category", ""),
                        "telephone": item.get("telephone", ""),
                        "mapx": mapx,
                        "mapy": mapy,
                        "link": item.get("link", ""),
                        "distance": distance,
                    })

            # 거리순 정렬 후 상위 N개만 반환
            results.sort(key=lambda x: x["distance"])
            return results[:display]

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        두 좌표 간 거리 계산 (미터 단위)
        Haversine formula 사용
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # 지구 반지름 (미터)

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

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

        # 네이버 검색 API가 설정되어 있지 않으면 에러
        if not self.search_client_id or not self.search_client_secret:
            raise ValueError("네이버 검색 API 키가 설정되지 않았습니다.")

        # 실제 API 호출
        places = await self.search_local(
            query=keyword,
            lat=lat,
            lng=lng,
            radius=1000,
            display=5
        )

        print(f"[INFO] Search API returned {len(places)} items for category: {category}")
        return places

    def _get_dummy_places(self, lat: float, lng: float, category: str) -> List[Dict[str, Any]]:
        """
        더미 주변 시설 데이터 반환 (데모/테스트용)
        실제 서비스에서는 네이버 검색 API 키를 발급받아 사용하세요.
        """
        dummy_data = {
            "subway": [
                {"name": "시청역 (1호선)", "address": "서울특별시 중구 세종대로 지하 101", "category": "지하철", "telephone": ""},
                {"name": "을지로입구역 (2호선)", "address": "서울특별시 중구 을지로 지하 23", "category": "지하철", "telephone": ""},
                {"name": "광화문역 (5호선)", "address": "서울특별시 종로구 종로 지하 172", "category": "지하철", "telephone": ""},
            ],
            "school": [
                {"name": "서울남산초등학교", "address": "서울특별시 중구 소파로 46", "category": "초등학교", "telephone": "02-555-1234"},
                {"name": "명동초등학교", "address": "서울특별시 중구 명동길 74", "category": "초등학교", "telephone": "02-555-5678"},
            ],
            "store": [
                {"name": "CU 시청점", "address": "서울특별시 중구 세종대로 110", "category": "편의점", "telephone": ""},
                {"name": "GS25 을지로점", "address": "서울특별시 중구 을지로 30", "category": "편의점", "telephone": ""},
                {"name": "세븐일레븐 명동점", "address": "서울특별시 중구 명동길 56", "category": "편의점", "telephone": ""},
            ],
            "hospital": [
                {"name": "서울대학교병원", "address": "서울특별시 종로구 대학로 101", "category": "종합병원", "telephone": "02-2072-2114"},
                {"name": "삼성서울병원", "address": "서울특별시 강남구 일원로 81", "category": "종합병원", "telephone": "02-3410-2114"},
            ],
            "park": [
                {"name": "남산공원", "address": "서울특별시 중구 삼일대로 231", "category": "공원", "telephone": "02-3783-5900"},
                {"name": "청계천", "address": "서울특별시 종로구 창신동", "category": "공원", "telephone": ""},
            ],
            "mart": [
                {"name": "롯데마트 서울역점", "address": "서울특별시 중구 한강대로 405", "category": "대형마트", "telephone": "02-390-2500"},
                {"name": "이마트 용산점", "address": "서울특별시 용산구 한강대로 23길 55", "category": "대형마트", "telephone": "02-2012-1234"},
            ],
        }

        places_list = dummy_data.get(category, [])

        # 더미 데이터에 mapx, mapy 추가 (대략적인 위치)
        results = []
        for idx, place in enumerate(places_list[:5]):
            # 위치를 약간씩 다르게 설정 (데모용)
            offset_lat = lat + (idx * 0.001)
            offset_lng = lng + (idx * 0.001)

            results.append({
                "name": place["name"],
                "address": place["address"],
                "category": place["category"],
                "telephone": place.get("telephone", ""),
                "mapx": str(int(offset_lng * 10000000)),
                "mapy": str(int(offset_lat * 10000000)),
                "link": "",
            })

        print(f"[INFO] Using dummy data for category: {category} ({len(results)} items)")
        return results


# 싱글톤 인스턴스
_naver_maps_service: Optional[NaverMapsService] = None


def get_naver_maps_service() -> NaverMapsService:
    """네이버 Maps 서비스 인스턴스 반환"""
    global _naver_maps_service
    if _naver_maps_service is None:
        _naver_maps_service = NaverMapsService()
    return _naver_maps_service
