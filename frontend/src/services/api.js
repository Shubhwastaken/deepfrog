import axios from "axios";
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
export const uploadDocument = async (formData) => (await axios.post(`${API_BASE}/api/upload`, formData)).data;
export const getResults = async (jobId) => (await axios.get(`${API_BASE}/api/results/${jobId}`)).data;
