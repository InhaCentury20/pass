import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { ApplicationDetail, ApplicationItem, ApplicationListResponse } from '@/types/api';

export const getApplications = async (): Promise<ApplicationListResponse> => {
  const { data } = await apiClient.get<ApplicationListResponse>(API_ENDPOINTS.APPLICATIONS.LIST);
  return data;
};

export const getApplicationDetail = async (applicationId: number): Promise<ApplicationDetail> => {
  const { data } = await apiClient.get<ApplicationDetail>(API_ENDPOINTS.APPLICATIONS.DETAIL(applicationId));
  return data;
};

export const createApplication = async (announcementId: number): Promise<ApplicationItem> => {
  const { data } = await apiClient.post<ApplicationItem>(API_ENDPOINTS.APPLICATIONS.CREATE, {
    announcement_id: announcementId,
  });
  return data;
};

