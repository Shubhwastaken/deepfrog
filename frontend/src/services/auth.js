import axios from "axios";
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const beginLogin = async (email, password) => {
  const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password });
  return res.data;
};

export const verifyOtp = async (challengeId, otpCode) => {
  const res = await axios.post(`${API_BASE}/api/auth/verify-otp`, {
    challenge_id: challengeId,
    otp_code: otpCode,
  });
  localStorage.setItem("token", res.data.access_token);
  if (res.data.user) {
    localStorage.setItem("auth_user", JSON.stringify(res.data.user));
  }
  return res.data;
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("auth_user");
};

export const getToken = () => localStorage.getItem("token");
export const isAuthenticated = () => Boolean(getToken());
export const getStoredUser = () => {
  const value = localStorage.getItem("auth_user");
  return value ? JSON.parse(value) : null;
};
