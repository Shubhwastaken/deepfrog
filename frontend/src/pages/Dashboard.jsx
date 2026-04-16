import React from "react";

import { Link } from "react-router-dom";

import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import { getRecentJobs } from "../utils/jobs";

export default function Dashboard() {
  const jobs = getRecentJobs();

  return (
    <AppShell
      title="Operations Dashboard"
      subtitle="Track recent customs jobs, reopen finished reports, and launch a new document review when the next shipment arrives."
    >
      <div className="hero-panel panel">
        <div className="metric-row">
          <div className="metric">
            <span className="metric-label">Recent Jobs</span>
            <div className="metric-value">{jobs.length}</div>
          </div>
          <div className="metric">
            <span className="metric-label">Completed</span>
            <div className="metric-value">{jobs.filter((job) => job.status === "completed").length}</div>
          </div>
          <div className="metric">
            <span className="metric-label">In Progress</span>
            <div className="metric-value">
              {jobs.filter((job) => job.status === "queued" || job.status === "processing").length}
            </div>
          </div>
          <div className="metric">
            <span className="metric-label">Failed</span>
            <div className="metric-value">{jobs.filter((job) => job.status === "failed").length}</div>
          </div>
        </div>
      </div>

      <div className="grid two">
        <div className="panel card">
          <span className="eyebrow">Start Here</span>
          <h2>Launch a new customs review</h2>
          <p className="muted">
            Upload the invoice and bill of lading together. The worker pipeline will extract data,
            generate HS code worlds, and produce a report-ready recommendation.
          </p>
          <div className="button-row">
            <Link className="button primary" to="/upload">
              New Upload
            </Link>
          </div>
        </div>
        <div className="panel card">
          <span className="eyebrow">What You Get</span>
          <h2>Decision-ready output</h2>
          <ul className="list">
            <li>Ranked HS code worlds with confidence, duty, risk, and compliance status.</li>
            <li>Plain-language winning recommendation for operations teams.</li>
            <li>Downloadable markdown report you can pass downstream for PDF generation.</li>
          </ul>
        </div>
      </div>

      <div className="panel card" style={{ marginTop: "24px" }}>
        <span className="eyebrow">Recent Activity</span>
        <h2>Recent jobs</h2>
        {jobs.length ? (
          <div className="job-list">
            {jobs.map((job) => (
              <div className="job-item" key={job.job_id}>
                <div>
                  <strong>{job.job_id}</strong>
                  <div className="muted">
                    Updated {job.last_updated_at ? new Date(job.last_updated_at).toLocaleString() : "just now"}
                  </div>
                </div>
                <div className="button-row">
                  <StatusBadge status={job.status} />
                  <Link className="button secondary" to={`/results/${job.job_id}`}>
                    Open Results
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="alert info">
            No jobs yet. Start with a shipment upload to populate the dashboard.
          </div>
        )}
      </div>
    </AppShell>
  );
}
