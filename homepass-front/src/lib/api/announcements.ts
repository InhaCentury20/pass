import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  Announcement,
  AnnouncementDetail,
  AnnouncementListResponse,
} from '@/types/api';

export interface AnnouncementQueryParams {
  page?: number;
  size?: number;
  region?: string;
  housing_type?: string;
  // Option A 서버 필터 파라미터
  exclude_past?: boolean;
  within_days?: number;
  // 정렬 파라미터
  order_by?: string; // e.g., 'post_date'
  order?: 'asc' | 'desc';
}

export const getAnnouncements = async (
  params: AnnouncementQueryParams = {},
  options?: { signal?: AbortSignal },
): Promise<AnnouncementListResponse> => {
  // 브라우저에서는 Next API 라우트 프록시로 호출하여 CORS 회피
  if (typeof window !== 'undefined') {
    const url = new URL('/api/proxy/announcements', window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, String(v));
      }
    });
    const primary = await fetch(url.toString(), { signal: options?.signal, cache: 'no-store' });
    if (primary.ok) {
      return primary.json();
    }
    // 1차 실패 시 바디를 읽어 업스트림 상태 확인
    let upstreamStatus: number | undefined;
    try {
      const errJson = await primary.json();
      upstreamStatus = errJson?.upstreamStatus;
    } catch {
      // ignore
    }
    // 백엔드가 exclude_past/within_days/order_by를 지원하지 않아 500이 나는 경우가 있음 → 완화 요청으로 재시도 후 프론트 필터/정렬
    if (upstreamStatus === 500 || primary.status === 500) {
      const relaxed = new URL('/api/proxy/announcements', window.location.origin);
      // exclude_past, within_days, order_by, order 제거
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '' && !['exclude_past', 'within_days', 'order_by', 'order'].includes(k)) {
          relaxed.searchParams.set(k, String(v));
        }
      });
      const res2 = await fetch(relaxed.toString(), { signal: options?.signal, cache: 'no-store' });
      if (res2.ok) {
        const data = (await res2.json()) as AnnouncementListResponse;
        // 프론트에서 30일 이내/정렬(post_date desc) 적용
        const now = new Date();
        const oneMonthLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
        const filtered = (data.items ?? []).filter((a) => {
          if (params.exclude_past === false) return true;
          const withinDays = params.within_days ?? 30;
          if (a.dday !== undefined && a.dday !== null) {
            return a.dday >= 0 && a.dday <= withinDays;
          }
          const end = a.application_end_date ? new Date(a.application_end_date) : undefined;
          if (end) {
            return end >= now && end <= oneMonthLater;
          }
          return false;
        });
        filtered.sort((a, b) => {
          const getDate = (x: any) =>
            new Date(x?.post_date ?? x?.scraped_at ?? x?.application_end_date ?? 0).getTime();
        return getDate(b) - getDate(a);
        });
        const size = Number(params.size ?? filtered.length);
        const items = filtered.slice(0, size);
        return {
          total: filtered.length,
          page: Number(params.page ?? 1),
          size,
          items,
        } as AnnouncementListResponse;
      }
    }
    // 실패 상세 메시지
    let detail = '';
    try {
      const json = await primary.json();
      detail =
        json?.upstreamStatus
          ? ` (upstream ${json.upstreamStatus}) ${json?.upstreamBody ?? ''}`
          : ` ${JSON.stringify(json).slice(0, 200)}`;
    } catch {
      // ignore
    }
    throw new Error(`Failed to fetch announcements via proxy: ${primary.status}${detail ? ' - ' + detail : ''}`);
  }
  // 서버 환경이면 직접 백엔드 호출
  const { data } = await apiClient.get<AnnouncementListResponse>(API_ENDPOINTS.ANNOUNCEMENTS.LIST, {
    params,
    signal: options?.signal,
    withCredentials: false,
  });
  return data;
};

export const getAnnouncementDetail = async (
  id: number,
): Promise<AnnouncementDetail> => {
  const { data } = await apiClient.get<AnnouncementDetail>(API_ENDPOINTS.ANNOUNCEMENTS.DETAIL(id));
  return data;
};

export const getAnnouncementByIdFromCache = (
  announcements: Announcement[],
  id: number,
): Announcement | undefined => announcements.find((item) => item.announcement_id === id);

