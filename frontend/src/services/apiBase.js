const configuredApiBase = process.env.REACT_APP_API_URL;
const browserApiBase =
  typeof window !== "undefined" && window.location.port === "3000"
    ? `http://${window.location.hostname}:8000`
    : "";

export const API_BASE =
  configuredApiBase && configuredApiBase.trim().length > 0
    ? configuredApiBase
    : browserApiBase;
