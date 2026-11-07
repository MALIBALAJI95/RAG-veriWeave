import axios, { AxiosError } from 'axios';

// Get base URL from environment or fallback to window.origin in dev/prod
const getBaseUrl = (): string => {
  // Use Vite env var if provided
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // In development, Vite dev proxy maps /api to http://localhost:8000
  return '';
};

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  timeout: 60000, // 60s timeout for local LLM inference / reranking
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ApiErrorDetails {
  message: string;
  statusCode?: number;
  detail?: string | Record<string, unknown>;
}

export const extractErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string | { msg?: string }[] }>;
    if (axiosError.response?.data?.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        return axiosError.response.data.detail;
      }
      if (Array.isArray(axiosError.response.data.detail)) {
        return axiosError.response.data.detail.map((e) => (typeof e === 'object' && e?.msg ? e.msg : JSON.stringify(e))).join(', ');
      }
      return JSON.stringify(axiosError.response.data.detail);
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected network or server error occurred.';
};
