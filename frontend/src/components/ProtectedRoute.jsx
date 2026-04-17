import React from "react";
import { Navigate, useLocation } from "react-router-dom";

import { getAuthUser, isAuthenticated } from "../services/auth";

export default function ProtectedRoute({ children, requireRole = null }) {
  const location = useLocation();
  const authUser = getAuthUser();

  if (!isAuthenticated()) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  if (requireRole && authUser?.role !== requireRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
