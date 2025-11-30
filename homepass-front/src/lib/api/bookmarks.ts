import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { Announcement } from '@/types/api';

export const toggleBookmark = async (id: number): Promise<{ success: boolean }> => {
  const { data } = await apiClient.post<{ success: boolean }>(API_ENDPOINTS.BOOKMARKS.TOGGLE(id));
  return data ?? { success: true };
};

type BookmarkResponse = Announcement[] | { items?: Announcement[] };

export const getMyBookmarks = async (): Promise<Announcement[]> => {
  const { data } = await apiClient.get<BookmarkResponse>(API_ENDPOINTS.BOOKMARKS.ME);
  if (Array.isArray(data)) {
    return data;
  }
  if ('items' in data && Array.isArray(data.items)) {
    return data.items;
  }
  return [];
};


