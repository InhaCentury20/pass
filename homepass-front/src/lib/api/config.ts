const PROD_BACKEND_URL = 'http://ec2-35-82-41-239.us-west-2.compute.amazonaws.com';
const DEFAULT_BACKEND_URL = process.env.NODE_ENV === 'production' ? PROD_BACKEND_URL : 'http://localhost:8000';

const PRIVATE_BACKEND_URL =
  process.env.BACKEND_API_URL ??
  process.env.API_BASE_URL ??
  process.env.INTERNAL_BACKEND_API_URL ??
  undefined;

const PUBLIC_BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  undefined;

export const serverBackendBaseUrl = PRIVATE_BACKEND_URL ?? PUBLIC_BACKEND_URL ?? DEFAULT_BACKEND_URL;
export const browserBackendBaseUrl = PUBLIC_BACKEND_URL ?? PRIVATE_BACKEND_URL ?? DEFAULT_BACKEND_URL;

export const resolveBackendBaseUrl = () =>
  (typeof window === 'undefined' ? serverBackendBaseUrl : browserBackendBaseUrl);


