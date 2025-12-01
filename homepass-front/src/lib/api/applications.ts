import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { ApplicationDetail, ApplicationListResponse } from '@/types/api';

export const getApplications = async (): Promise<ApplicationListResponse> => {
  const { data } = await apiClient.get<ApplicationListResponse>(API_ENDPOINTS.APPLICATIONS.LIST);
  return data;
};

export const getApplicationDetail = async (applicationId: number): Promise<ApplicationDetail> => {
  const { data } = await apiClient.get<ApplicationDetail>(API_ENDPOINTS.APPLICATIONS.DETAIL(applicationId));
  return data;
};

