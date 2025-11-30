import { clientBackendBaseUrl } from './config';
import type { NearbyPlacesResponse } from '@/types/api';

/**
 * 주변 시설 조회
 */
export async function getNearbyPlaces(
  lat: number,
  lng: number,
  category: string
): Promise<NearbyPlacesResponse> {
  const params = new URLSearchParams({
    lat: lat.toString(),
    lng: lng.toString(),
    category,
  });

  const res = await fetch(`${clientBackendBaseUrl}/api/v1/places/nearby?${params}`);

  if (!res.ok) {
    throw new Error('주변 시설 조회에 실패했습니다');
  }

  return res.json();
}
