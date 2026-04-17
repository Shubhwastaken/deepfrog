import axios from "axios";

import { API_BASE } from "./apiBase";

const AUTH_USER_KEY = "auth_user";
const ACCESS_TOKEN_KEY = "token";
const REFRESH_TOKEN_KEY = "refresh_token";

export const clearSession = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
};

export const setSession = ({ access_token, refresh_token, user }) => {
  if (access_token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
  }
  if (refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
  }
  if (user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  }
};

export const beginLogin = async (email, password) => {
  const res = await axios.post(`${API_BASE}/api/auth/login`, { email, password });
  return res.data;
};

export const getAuthProviders = async () => {
  const res = await axios.get(`${API_BASE}/api/auth/providers`);
  return res.data;
};

export const loginWithGoogle = async (credential) => {
  const res = await axios.post(`${API_BASE}/api/auth/google`, { credential });
  setSession(res.data);
  return res.data;
};

export const verifyOtp = async (challengeId, otpCode) => {
  const res = await axios.post(`${API_BASE}/api/auth/verify-otp`, {
    challenge_id: challengeId,
    otp_code: otpCode,
  });
  setSession(res.data);
  return res.data;
};

export const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  const res = await axios.post(`${API_BASE}/api/auth/refresh`, {
    refresh_token: refreshToken,
  });
  setSession(res.data);
  return res.data;
};

export const logout = () => {
  clearSession();
};

export const getToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);
export const getAuthUser = () => {
  const rawUser = localStorage.getItem(AUTH_USER_KEY);
  return rawUser ? JSON.parse(rawUser) : null;
};
export const isAuthenticated = () => Boolean(getToken() || getRefreshToken());
