import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type { UserProfileResponse } from '@/types/api';

export interface LoginPayload {
  email: string;
  password: string;
}

export const login = async (payload: LoginPayload): Promise<UserProfileResponse | { message?: string }> => {
  const { data } = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, payload);
  return data;
};

export const logout = async (): Promise<{ message?: string }> => {
  const { data } = await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
  return data ?? {};
};


