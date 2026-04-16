import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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
