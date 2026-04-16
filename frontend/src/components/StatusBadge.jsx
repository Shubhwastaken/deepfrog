import React from "react";

export default function StatusBadge({ status }) {
  const safeStatus = status || "queued";
  return <span className={`status-badge ${safeStatus}`}>{safeStatus}</span>;
}
