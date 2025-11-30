// API 엔드포인트 상수 정의

export const API_ENDPOINTS = {
  // 사용자 관련
  USERS: {
    ME: '/api/v1/users/me',
    PERSONAL_INFO: '/api/v1/users/me/personal-info',
    SUBSCRIPTION_INFO: '/api/v1/users/me/subscription-info',
    PREFERENCES: '/api/v1/users/me/preferences',
    AUTO_APPLY_MODE: '/api/v1/users/me/auto-apply-mode',
    NOTIFICATION_SETTINGS: '/api/v1/users/me/notification-settings',
  },
  
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
  },
  
  // 공고 관련
  ANNOUNCEMENTS: {
    LIST: '/api/v1/announcements',
    DETAIL: (id: number) => `/api/v1/announcements/${id}`,
    SCRAPE: '/api/v1/announcements/scrape',
  },
  
  // 신청 관련
  APPLICATIONS: {
    LIST: '/api/v1/applications',
    DETAIL: (id: number) => `/api/v1/applications/${id}`,
    CREATE: '/api/v1/applications',
  },
  
  // 알림 관련
  NOTIFICATIONS: {
    LIST: '/api/v1/notifications',
    MARK_READ: '/api/v1/notifications/read',
    MARK_ONE: (id: number) => `/api/v1/notifications/${id}/read`,
  },
  
  // 기타
  PLACES: {
    NEARBY: '/api/v1/places/nearby',
  },
  
  // 북마크 관련
  BOOKMARKS: {
    TOGGLE: (id: number) => `/api/v1/bookmarks/${id}`,
    ME: '/api/v1/bookmarks/me',
  },
  
  CHATBOT: {
    QUERY: '/api/v1/chatbot/query',
  },
} as const;

