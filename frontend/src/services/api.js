import axios from "axios";

import { API_BASE } from "./apiBase";
import { clearSession, getRefreshToken, getToken, refreshAccessToken } from "./auth";

const api = axios.create({
  baseURL: API_BASE,
});

let refreshPromise = null;

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const statusCode = error?.response?.status;
    const detail = error?.response?.data?.detail;
    const originalRequest = error?.config || {};
    const isRefreshCall = originalRequest?.url?.includes("/api/auth/refresh");
    const canRefresh = Boolean(getRefreshToken()) && !originalRequest._retry && !isRefreshCall;
    const shouldRefresh =
      statusCode === 401 &&
      canRefresh &&
      ["Invalid access token", "Authentication required", "Invalid access token payload", "User not found"].includes(
        detail
      );

    if (shouldRefresh) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        await refreshPromise;
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${getToken()}`;
        return api(originalRequest);
      } catch (refreshError) {
        clearSession();
        if (typeof window !== "undefined" && window.location.pathname !== "/") {
          window.location.href = "/";
        }
        return Promise.reject(refreshError);
      }
    }

    if (statusCode === 401 && (detail === "Invalid access token" || detail === "Authentication required")) {
      clearSession();
      if (typeof window !== "undefined" && window.location.pathname !== "/") {
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  }
);

export async function uploadDocuments({ invoiceFile, billOfLadingFile }) {
  const formData = new FormData();
  formData.append("invoice", invoiceFile);
  formData.append("bill_of_lading", billOfLadingFile);
  const response = await api.post("/api/upload", formData);
  return response.data;
}

export async function getResults(jobId) {
  const response = await api.get(`/api/results/${jobId}`);
  return response.data;
}

export async function getPipelineMetrics() {
  const response = await api.get("/api/metrics/pipeline");
  return response.data;
}

export async function getSecurityStorageProof() {
  const response = await api.get("/api/security/storage");
  return response.data;
}

export async function downloadReport(jobId) {
  const response = await api.get(`/api/results/${jobId}/report`, { responseType: "blob" });
  return response.data;
}

export function getReportDownloadUrl(jobId) {
  return `${API_BASE}/api/results/${jobId}/report`;
}

export function getApiErrorMessage(error, fallbackMessage) {
  return error?.response?.data?.detail || error?.message || fallbackMessage;
}
