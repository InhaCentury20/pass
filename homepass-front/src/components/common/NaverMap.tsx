'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getNearbyPlaces } from '@/lib/api/places';
import type { Place, CommuteInfo } from '@/types/api';

// Naver Maps API 타입 정의
interface NaverMapsAPI {
  maps: {
    LatLng: new (lat: number, lng: number) => NaverLatLng;
    Map: new (element: HTMLElement, options: MapOptions) => NaverMap;
    Marker: new (options: MarkerOptions) => NaverMarker;
    InfoWindow: new (options: InfoWindowOptions) => NaverInfoWindow;
    Polyline: new (options: PolylineOptions) => NaverPolyline;
    Point: new (x: number, y: number) => NaverPoint;
    Position: {
      TOP_RIGHT: number;
    };
    Event: {
      addListener: (target: NaverMarker, event: string, handler: () => void) => void;
    };
  };
}

// Naver LatLng instance (opaque type)
type NaverLatLng = object;

// Naver Map instance (opaque type)
type NaverMap = object;

interface NaverMarker {
  setMap: (map: NaverMap | null) => void;
}

interface NaverInfoWindow {
  getMap: () => NaverMap | null;
  close: () => void;
  open: (map: NaverMap, marker: NaverMarker) => void;
}

interface NaverPolyline {
  setMap: (map: NaverMap | null) => void;
}

// Naver Point instance (opaque type)
type NaverPoint = object;

interface MapOptions {
  center: NaverLatLng;
  zoom: number;
  zoomControl: boolean;
  zoomControlOptions: {
    position: number;
  };
}

interface MarkerOptions {
  position: NaverLatLng;
  map: NaverMap;
  title: string;
  icon?: {
    content: string;
    anchor: NaverPoint;
  };
}

interface InfoWindowOptions {
  content: string;
}

interface PolylineOptions {
  map: NaverMap;
  path: NaverLatLng[];
  strokeColor?: string;
  strokeWeight?: number;
  strokeOpacity?: number;
  strokeStyle?: string;
}

declare global {
  interface Window {
    naver?: NaverMapsAPI;
  }
}

interface NaverMapProps {
  latitude: number;
  longitude: number;
  selectedCategory?: string;
  onCategoryChange?: (category: string) => void;
  commuteInfo?: CommuteInfo | null;
}

// 네이버 Maps API 스크립트를 동적으로 로드
function loadNaverMapScript(clientId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window !== 'undefined' && window.naver?.maps) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${clientId}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('네이버 지도 스크립트 로드 실패'));
    document.head.appendChild(script);
  });
}

export default function NaverMap({
  latitude,
  longitude,
  selectedCategory = 'subway',
  commuteInfo = null,
}: NaverMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<NaverMap | null>(null);
  const markersRef = useRef<NaverMarker[]>([]);
  const polylineRef = useRef<NaverPolyline | null>(null);
  const commuteMarkersRef = useRef<NaverMarker[]>([]); // 출발지/도착지 마커
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState<string | null>(null);

  // 주변 시설 데이터 조회
  const { data: nearbyData, isLoading } = useQuery({
    queryKey: ['nearby-places', latitude, longitude, selectedCategory],
    queryFn: () => getNearbyPlaces(latitude, longitude, selectedCategory),
    enabled: scriptLoaded && !!latitude && !!longitude,
    staleTime: 5 * 60 * 1000, // 5분
  });

  // 네이버 Maps 스크립트 로드
  useEffect(() => {
    const clientId = process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID || process.env.NAVER_MAP_CLIENT_ID;

    if (!clientId) {
      // 비동기로 에러 설정하여 effect 규칙 준수
      Promise.resolve().then(() =>
        setScriptError('네이버 지도 Client ID가 설정되지 않았습니다')
      );
      return;
    }

    loadNaverMapScript(clientId)
      .then(() => setScriptLoaded(true))
      .catch((err) => setScriptError(err.message));
  }, []);

  // 지도 초기화
  useEffect(() => {
    if (!scriptLoaded || !mapRef.current || map || !window.naver) return;

    const naver = window.naver;
    const center = new naver.maps.LatLng(latitude, longitude);

    const mapInstance = new naver.maps.Map(mapRef.current, {
      center,
      zoom: 15,
      zoomControl: true,
      zoomControlOptions: {
        position: naver.maps.Position.TOP_RIGHT,
      },
    });

    // 주택 위치 마커 (메인)
    new naver.maps.Marker({
      position: center,
      map: mapInstance,
      title: '주택 위치',
      icon: {
        content: `
          <div style="
            background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
            border: 3px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            font-size: 20px;
          ">🏠</div>
        `,
        anchor: new naver.maps.Point(20, 20),
      },
    });

    setMap(mapInstance);
  }, [scriptLoaded, latitude, longitude, map]);

  // 주변 시설 마커 표시
  useEffect(() => {
    if (!map || !nearbyData?.places || !window.naver) return;

    const naver = window.naver;

    // 기존 마커 제거
    markersRef.current.forEach((marker) => marker.setMap(null));

    // 카테고리별 아이콘 설정
    const categoryIcons: Record<string, string> = {
      subway: '🚇',
      school: '🏫',
      store: '🏪',
      hospital: '🏥',
      park: '🌳',
      mart: '🛒',
    };

    const icon = categoryIcons[selectedCategory] || '📍';

    // 새 마커 생성
    const newMarkers = nearbyData.places.map((place: Place) => {
      // 네이버 좌표계를 WGS84로 변환 (간단한 근사)
      // 실제로는 더 정확한 변환이 필요할 수 있음
      const lat = place.mapy ? parseFloat(place.mapy) / 10000000 : latitude;
      const lng = place.mapx ? parseFloat(place.mapx) / 10000000 : longitude;

      const marker = new naver.maps.Marker({
        position: new naver.maps.LatLng(lat, lng),
        map,
        title: place.name,
        icon: {
          content: `
            <div style="
              background: white;
              border: 2px solid #6366f1;
              border-radius: 50%;
              width: 32px;
              height: 32px;
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 2px 4px rgba(0,0,0,0.15);
              font-size: 16px;
            ">${icon}</div>
          `,
          anchor: new naver.maps.Point(16, 16),
        },
      });

      // 정보창
      const infoWindow = new naver.maps.InfoWindow({
        content: `
          <div style="padding: 12px; min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; font-weight: bold; font-size: 14px;">${place.name}</h4>
            <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">${place.address}</p>
            ${place.telephone ? `<p style="margin: 0; font-size: 12px; color: #666;">☎️ ${place.telephone}</p>` : ''}
          </div>
        `,
      });

      naver.maps.Event.addListener(marker, 'click', () => {
        if (infoWindow.getMap()) {
          infoWindow.close();
        } else {
          infoWindow.open(map, marker);
        }
      });

      return marker;
    });

    // 마커 참조 저장
    markersRef.current = newMarkers;

    // Cleanup: 컴포넌트 언마운트 시 또는 의존성 변경 시 마커 제거
    return () => {
      newMarkers.forEach((marker) => marker.setMap(null));
    };
  }, [map, nearbyData, selectedCategory, latitude, longitude]);

  // 출퇴근 경로 그리기
  useEffect(() => {
    if (!map || !commuteInfo?.path || !window.naver) return;

    const naver = window.naver;

    // 기존 경로선 및 마커 제거
    if (polylineRef.current) {
      polylineRef.current.setMap(null);
    }
    commuteMarkersRef.current.forEach((marker) => marker.setMap(null));
    commuteMarkersRef.current = [];

    // path 좌표를 NaverLatLng 배열로 변환
    const pathCoords = commuteInfo.path.map(
      ([lat, lng]) => new naver.maps.LatLng(lat, lng)
    );

    // 경로선 생성
    const polyline = new naver.maps.Polyline({
      map,
      path: pathCoords,
      strokeColor: '#5347ec', // 보라색 계열
      strokeWeight: 5,
      strokeOpacity: 0.8,
      strokeStyle: 'solid',
    });

    polylineRef.current = polyline;

    // 출발지 마커 (경로의 첫 번째 지점)
    if (commuteInfo.path.length > 0) {
      const [startLat, startLng] = commuteInfo.path[0];
      const startMarker = new naver.maps.Marker({
        position: new naver.maps.LatLng(startLat, startLng),
        map,
        title: '출발지',
        icon: {
          content: `
            <div style="
              position: relative;
              width: 60px;
              height: 60px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
            ">
              <div style="
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                border: 3px solid white;
                border-radius: 50%;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
                font-size: 22px;
              ">🏁</div>
              <div style="
                margin-top: 2px;
                background: white;
                color: #059669;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                white-space: nowrap;
              ">출발</div>
            </div>
          `,
          anchor: new naver.maps.Point(30, 30),
        },
      });
      commuteMarkersRef.current.push(startMarker);
    }

    // 도착지 마커 (경로의 마지막 지점)
    if (commuteInfo.path.length > 1) {
      const [endLat, endLng] = commuteInfo.path[commuteInfo.path.length - 1];
      const endMarker = new naver.maps.Marker({
        position: new naver.maps.LatLng(endLat, endLng),
        map,
        title: '도착지',
        icon: {
          content: `
            <div style="
              position: relative;
              width: 60px;
              height: 60px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
            ">
              <div style="
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                border: 3px solid white;
                border-radius: 50%;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
                font-size: 22px;
              ">🎯</div>
              <div style="
                margin-top: 2px;
                background: white;
                color: #dc2626;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                white-space: nowrap;
              ">도착</div>
            </div>
          `,
          anchor: new naver.maps.Point(30, 30),
        },
      });
      commuteMarkersRef.current.push(endMarker);
    }

    // Cleanup: 컴포넌트 언마운트 시 또는 의존성 변경 시 경로선 및 마커 제거
    return () => {
      if (polylineRef.current) {
        polylineRef.current.setMap(null);
      }
      commuteMarkersRef.current.forEach((marker) => marker.setMap(null));
    };
  }, [map, commuteInfo]);

  if (scriptError) {
    return (
      <div className="aspect-video bg-red-50 rounded-xl flex items-center justify-center border-2 border-red-300 text-red-600 p-4 text-center">
        <div>
          <div className="text-4xl mb-2">⚠️</div>
          <div className="text-sm">{scriptError}</div>
        </div>
      </div>
    );
  }

  if (!latitude || !longitude) {
    return (
      <div className="aspect-video bg-yellow-50 rounded-xl flex items-center justify-center border-2 border-yellow-300 text-yellow-600 p-4 text-center">
        <div>
          <div className="text-4xl mb-2">📍</div>
          <div className="text-sm">위치 정보가 없습니다</div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <div ref={mapRef} className="aspect-video rounded-xl overflow-hidden shadow-lg" />

      {isLoading && (
        <div className="absolute top-4 right-4 bg-white px-4 py-2 rounded-lg shadow-lg text-sm text-gray-600 flex items-center gap-2">
          <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          주변 시설 검색 중...
        </div>
      )}

      {nearbyData && !isLoading && (
        <div className="absolute bottom-4 left-4 bg-white px-4 py-2 rounded-lg shadow-lg text-xs text-gray-600">
          {nearbyData.places.length}개의 시설 발견
        </div>
      )}
    </div>
  );
}
