import axios from "axios";

const configuredApiBase = process.env.REACT_APP_API_URL;
const API_BASE =
  configuredApiBase !== undefined
    ? configuredApiBase
    : window.location.port === "3000"
      ? "http://localhost:8000"
      : "";

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
  return res.data;
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("auth_user");
};

export const getToken = () => localStorage.getItem("token");
export const isAuthenticated = () => Boolean(getToken());
