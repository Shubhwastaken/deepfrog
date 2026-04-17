import React from "react";
import { NavLink } from "react-router-dom";

import { getAuthUser, logout } from "../services/auth";

export default function AppShell({ title, subtitle, children, showLogout = true }) {
  const authUser = getAuthUser();
  const isAdmin = authUser?.role === "admin";

  return (
    <div className="app-shell">
      <div className="app-frame">
        <div className="topbar">
          <div className="brand-block">
            <span className="eyebrow">Customs Brain</span>
            <h1 className="brand-title">{title}</h1>
            <p className="brand-subtitle">{subtitle}</p>
          </div>
          <div className="nav-pills">
            <NavLink to="/dashboard" className={({ isActive }) => `nav-pill${isActive ? " active" : ""}`}>
              Dashboard
            </NavLink>
            <NavLink to="/upload" className={({ isActive }) => `nav-pill${isActive ? " active" : ""}`}>
              New Job
            </NavLink>
            {isAdmin ? (
              <NavLink to="/security" className={({ isActive }) => `nav-pill${isActive ? " active" : ""}`}>
                Security
              </NavLink>
            ) : null}
            {showLogout ? (
              <button
                className="nav-pill"
                onClick={() => {
                  logout();
                  window.location.href = "/";
                }}
                type="button"
              >
                Logout
              </button>
            ) : null}
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}
