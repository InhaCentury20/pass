// API 응답 타입 정의

export interface User {
  user_id: number;
  email: string;
  name: string;
  phone_number?: string;
  address?: string;
  created_at: string;
}

export interface SubscriptionInfo {
  info_id: number;
  user_id: number;
  bank_name?: string;
  join_date?: string;
  payment_count?: number;
  total_payment_amount?: number;
  is_household_head?: boolean;
  income_level_percent?: number;
  updated_at?: string;
}

export interface Preference {
  pref_id: number;
  user_id: number;
  locations?: string[];
  housing_types?: string[];
  min_area?: number;
  max_area?: number;
  max_deposit?: number;
  max_monthly_rent?: number;
  commute_base_address?: string;
  max_commute_time_minutes?: number;
  auto_apply_mode?: 'full_auto' | 'approval' | 'disabled';
  updated_at?: string;
}

export interface PriceOption {
  type?: string;
  deposit_ratio?: string;
  supply_type_primary?: string;
  supply_type_secondary?: string;
  deposit_amount?: number;
  rent_amount?: number;
}

export interface Announcement {
  announcement_id: number;
  title: string;
  housing_type?: string;
  region?: string;
  address_detail?: string;
  source_organization?: string;
  source_url?: string;
  original_pdf_url?: string;
  latitude?: number;
  longitude?: number;
  application_end_date?: string;
  scraped_at?: string;
  post_date?: string; // 게시일(백엔드 제공 시 정렬 우선 사용)
  min_deposit?: number;
  max_deposit?: number;
  monthly_rent?: number;
  total_households?: number;
  eligibility?: string;
  commute_base_address?: string;
  commute_time?: number;
  image_urls: string[];
  is_customized: boolean;
  dday?: number;
  price?: PriceOption[];
}

export type AnnouncementSchedule =
  | Array<{ date: string; event: string }>
  | Record<string, string>
  | string
  | null
  | undefined;

export interface AnnouncementDetail extends Announcement {
  schedules?: AnnouncementSchedule;
}

export interface AnnouncementListResponse {
  total: number;
  page: number;
  size: number;
  items: Announcement[];
}

export interface ApplicationItem {
  application_id: number;
  announcement_id: number;
  announcement_title: string;
  status: 'applied' | 'document_review' | 'won' | 'failed';
  applied_at?: string;
  status_updated_at?: string;
  dday?: number;
  housing_type?: string;
  region?: string;
  image_url?: string;
}

export interface ApplicationAnnouncementSummary {
  announcement_id: number;
  title: string;
  housing_type?: string;
  region?: string;
  application_end_date?: string;
  source_url?: string;
  application_link?: string;
  image_urls: string[];
  min_deposit?: number;
  max_deposit?: number;
  monthly_rent?: number;
  eligibility?: string;
}

export interface ApplicationDetail extends ApplicationItem {
  announcement_detail?: ApplicationAnnouncementSummary;
}

export interface ApplicationListResponse {
  total: number;
  items: ApplicationItem[];
}

export interface NotificationItem {
  notification_id: number;
  announcement_id?: number;
  category: string;
  message: string;
  is_read: boolean;
  created_at?: string;
  announcement_title?: string;
  image_url?: string;
}

export interface NotificationListResponse {
  total: number;
  unread_count: number;
  items: NotificationItem[];
}

export interface PersonalInfoResponse {
  message: string;
  data: User;
}

export interface SubscriptionInfoPayload {
  bank_name?: string;
  join_date?: string;
  payment_count?: number;
  total_payment_amount?: number;
  is_household_head?: boolean;
  income_level_percent?: number;
}

export interface PreferencePayload {
  locations?: string[];
  housing_types?: string[];
  min_area?: number;
  max_area?: number;
  max_deposit?: number;
  max_monthly_rent?: number;
  commute_base_address?: string;
  max_commute_time_minutes?: number;
  auto_apply_mode?: 'full_auto' | 'approval' | 'disabled';
}

export interface NotificationSetting {
  id: number;
  user_id: number;
  new_announcement: boolean;
  auto_apply_complete: boolean;
  dday: boolean;
  result: boolean;
  updated_at?: string;
}

export interface NotificationSettingPayload {
  new_announcement?: boolean;
  auto_apply_complete?: boolean;
  dday?: boolean;
  result?: boolean;
}

export interface UserProfileResponse {
  message: string;
  user: User;
  subscription?: SubscriptionInfo;
  preference?: Preference;
  notification?: NotificationSetting;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// 주변 시설 관련 타입
export interface Place {
  name: string;
  address: string;
  category?: string;
  telephone?: string;
  mapx?: string;
  mapy?: string;
  link?: string;
}

export interface NearbyPlacesResponse {
  center: {
    lat: number;
    lng: number;
  };
  category: string;
  places: Place[];
}

// 출퇴근 정보 타입
export interface CommuteInfo {
  start_address: string;  // 출발지 주소 (공고 주소)
  end_address: string;    // 도착지 주소 (유저 주소)
  distance: number;       // 거리 (미터)
  duration: number;       // 소요 시간 (밀리초)
  duration_minutes: number; // 소요 시간 (분)
  path: number[][];       // 경로 좌표 [[lat, lng], ...]
}

