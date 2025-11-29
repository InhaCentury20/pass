import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { Announcement } from '@/types/api';

export const toggleBookmark = async (id: number): Promise<{ success: boolean }> => {
  const { data } = await apiClient.post<{ success: boolean }>(API_ENDPOINTS.BOOKMARKS.TOGGLE(id));
  return data ?? { success: true };
};

export const getMyBookmarks = async (): Promise<Announcement[]> => {
  const { data } = await apiClient.get(API_ENDPOINTS.BOOKMARKS.ME);
  // 응답 형태가 { items: Announcement[] } 또는 Announcement[] 인 경우 모두 지원
  if (Array.isArray(data)) {
    return data as Announcement[];
  }
  if (Array.isArray((data as any)?.items)) {
    return (data as any).items as Announcement[];
  }
  return [];
};


