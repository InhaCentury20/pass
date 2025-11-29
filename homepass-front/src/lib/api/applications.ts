import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { ApplicationListResponse } from '@/types/api';

export const getApplications = async (): Promise<ApplicationListResponse> => {
  const { data } = await apiClient.get<ApplicationListResponse>(API_ENDPOINTS.APPLICATIONS.LIST);
  return data;
};

