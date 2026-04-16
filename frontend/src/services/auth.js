import axios from "axios";
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
export const login = async (email, password) => {
  const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password });
  localStorage.setItem("token", res.data.access_token);
  return res.data;
};
export const logout = () => localStorage.removeItem("token");
export const getToken = () => localStorage.getItem("token");
