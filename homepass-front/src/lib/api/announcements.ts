import axios from 'axios';
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
  const callBackend = async (query: AnnouncementQueryParams) => {
    const { data } = await apiClient.get<AnnouncementListResponse>(API_ENDPOINTS.ANNOUNCEMENTS.LIST, {
      params: query,
      signal: options?.signal,
      withCredentials: typeof window !== 'undefined',
    });
    return data;
  };

  try {
    return await callBackend(params);
  } catch (error) {
    const axiosError = axios.isAxiosError(error) ? error : null;
    const status = axiosError?.response?.status;

    // 백엔드가 특정 필터를 지원하지 않을 때 500이 발생 → 완화 요청 후 프론트에서 후처리
    if (status === 500) {
      type Defined<T> = Exclude<T, undefined>;
      const relaxedParams: Partial<{ [K in keyof AnnouncementQueryParams]: Defined<AnnouncementQueryParams[K]> }> =
        {};
      for (const key of Object.keys(params) as (keyof AnnouncementQueryParams)[]) {
        const value = params[key];
        if (
          value !== undefined &&
          value !== null &&
          value !== '' &&
          !['exclude_past', 'within_days', 'order_by', 'order'].includes(key)
        ) {
          relaxedParams[key] = value as Defined<AnnouncementQueryParams[typeof key]>;
        }
      }

      try {
        const relaxedData = await callBackend(relaxedParams);
        // 프론트에서 30일 이내/정렬(post_date desc) 적용
        const now = new Date();
        const oneMonthLater = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
        const filtered = (relaxedData.items ?? []).filter((a: Announcement) => {
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
          const getDate = (announcement: Announcement) =>
            new Date(
              announcement.post_date ?? announcement.scraped_at ?? announcement.application_end_date ?? 0,
            ).getTime();
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
      } catch (relaxedError) {
        // fallback 실패 시 아래 공통 에러 처리
        error = relaxedError;
      }
    }

    const detail = axiosError
      ? ` (status ${axiosError.response?.status ?? 'unknown'}) ${
          typeof axiosError.response?.data === 'string'
            ? axiosError.response?.data
            : JSON.stringify(axiosError.response?.data ?? {}).slice(0, 200)
        }`
      : ` ${String(error)}`;

    throw new Error(`Failed to fetch announcements${detail}`);
  }
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


