import apiClient from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  PersonalInfoResponse,
  SubscriptionInfo,
  SubscriptionInfoPayload,
  Preference,
  PreferencePayload,
  NotificationSetting,
  NotificationSettingPayload,
  UserProfileResponse,
} from '@/types/api';

export interface PersonalInfoUpdatePayload {
  email?: string;
  password?: string;
  name?: string;
  phone_number?: string;
  address?: string;
}

export const fetchUserProfile = async (): Promise<UserProfileResponse> => {
  const { data } = await apiClient.get<UserProfileResponse>(API_ENDPOINTS.USERS.ME);
  return data;
};

export const updatePersonalInfo = async (
  payload: PersonalInfoUpdatePayload,
): Promise<PersonalInfoResponse> => {
  const { data } = await apiClient.put<PersonalInfoResponse>(
    API_ENDPOINTS.USERS.PERSONAL_INFO,
    payload,
  );
  return data;
};

export const updateSubscriptionInfo = async (
  payload: SubscriptionInfoPayload,
): Promise<SubscriptionInfo> => {
  const { data } = await apiClient.put<SubscriptionInfo>(
    API_ENDPOINTS.USERS.SUBSCRIPTION_INFO,
    payload,
  );
  return data;
};

export const updatePreferences = async (
  payload: PreferencePayload,
): Promise<Preference> => {
  const { data } = await apiClient.put<Preference>(
    API_ENDPOINTS.USERS.PREFERENCES,
    payload,
  );
  return data;
};

export const updateNotificationSettings = async (
  payload: NotificationSettingPayload,
): Promise<NotificationSetting> => {
  const { data } = await apiClient.put<NotificationSetting>(
    API_ENDPOINTS.USERS.NOTIFICATION_SETTINGS,
    payload,
  );
  return data;
};

