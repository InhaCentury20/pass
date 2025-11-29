import axios from 'axios';
import { resolveBackendBaseUrl } from './config';

const API_BASE_URL = resolveBackendBaseUrl();

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 30000,
});

export default apiClient;

