import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { NotificationListResponse } from '@/types/api';

export const getNotifications = async (): Promise<NotificationListResponse> => {
  const { data } = await apiClient.get<NotificationListResponse>(API_ENDPOINTS.NOTIFICATIONS.LIST);
  return data;
};

export const markNotificationsAsRead = async (): Promise<NotificationListResponse> => {
  const { data } = await apiClient.post<NotificationListResponse>(API_ENDPOINTS.NOTIFICATIONS.MARK_READ);
  return data;
};

export const markNotificationAsRead = async (id: number): Promise<void> => {
  try {
    await apiClient.post(API_ENDPOINTS.NOTIFICATIONS.MARK_ONE(id));
    return;
  } catch (error) {
    // Fallback: 서버가 개별 엔드포인트를 지원하지 않으면 ids 배열로 시도
    try {
      await apiClient.post(API_ENDPOINTS.NOTIFICATIONS.MARK_READ, { ids: [id] });
      return;
    } catch {
      throw error;
    }
  }
};

