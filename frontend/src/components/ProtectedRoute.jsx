import React from "react";
import { Navigate, useLocation } from "react-router-dom";

import { isAuthenticated } from "../services/auth";

export default function ProtectedRoute({ children }) {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return children;
}
