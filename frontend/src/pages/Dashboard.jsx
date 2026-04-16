import React, { useEffect, useState } from "react";

import { Link } from "react-router-dom";

import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import { getPipelineMetrics } from "../services/api";
import { getRecentJobs } from "../utils/jobs";

export default function Dashboard() {
  const jobs = getRecentJobs();
  const [pipelineMetrics, setPipelineMetrics] = useState(null);
  const [metricsError, setMetricsError] = useState("");

  useEffect(() => {
    let pollTimer;
    let cancelled = false;

    async function loadMetrics() {
      try {
        const response = await getPipelineMetrics();
        if (cancelled) {
          return;
        }
        setPipelineMetrics(response);
        setMetricsError("");
        pollTimer = window.setTimeout(loadMetrics, 5000);
      } catch (error) {
        if (!cancelled) {
          setMetricsError(error?.response?.data?.detail || "Could not load worker metrics.");
        }
      }
    }

    loadMetrics();

    return () => {
      cancelled = true;
      if (pollTimer) {
        window.clearTimeout(pollTimer);
      }
    };
  }, []);

  const workers = pipelineMetrics?.workers || [];
  const workerEvents = pipelineMetrics?.recent_worker_events || [];
  const parallelLabel = pipelineMetrics?.parallel_processing_live
    ? "Live"
    : pipelineMetrics?.parallel_capacity_ready
      ? "Ready"
      : "Offline";

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
          <div className="metric">
            <span className="metric-label">Active Workers</span>
            <div className="metric-value">{pipelineMetrics?.active_workers ?? "--"}</div>
          </div>
          <div className="metric">
            <span className="metric-label">Busy Workers</span>
            <div className="metric-value">{pipelineMetrics?.busy_workers ?? "--"}</div>
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

      <div className="grid two" style={{ marginTop: "24px" }}>
        <div className="panel card">
          <span className="eyebrow">Worker Fleet</span>
          <h2>Parallel execution status</h2>
          <p className="muted">
            The queue is ready for parallel processing when two workers are alive. It is live only when both are busy at
            the same time on different jobs.
          </p>
          <div className="signal-strip" style={{ marginTop: "14px" }}>
            <span className={`signal-pill ${
              parallelLabel === "Live" ? "good" : parallelLabel === "Ready" ? "warning" : "danger"
            }`}>
              Parallel {parallelLabel}
            </span>
            <span className="signal-pill neutral">Queue depth {pipelineMetrics?.queued ?? "--"}</span>
            <span className="signal-pill neutral">Completed {pipelineMetrics?.completed ?? "--"}</span>
          </div>
          {metricsError ? <div className="alert error" style={{ marginTop: "16px" }}>{metricsError}</div> : null}
          {workers.length ? (
            <div className="worker-grid">
              {workers.map((worker) => (
                <div className={`worker-card ${worker.status}`} key={worker.worker_name}>
                  <div className="worker-card-top">
                    <div>
                      <strong>{worker.worker_name}</strong>
                      <div className="muted">{worker.service_name}</div>
                    </div>
                    <StatusBadge status={worker.status === "busy" ? "processing" : worker.status} />
                  </div>
                  <div className="worker-stat-list">
                    <div>
                      <span className="metric-label">Current job</span>
                      <strong>{worker.current_job_id || "Idle"}</strong>
                    </div>
                    <div>
                      <span className="metric-label">Completed</span>
                      <strong>{worker.jobs_completed}</strong>
                    </div>
                    <div>
                      <span className="metric-label">Failed</span>
                      <strong>{worker.jobs_failed}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="alert info" style={{ marginTop: "16px" }}>
              No active workers are publishing heartbeats yet.
            </div>
          )}
        </div>

        <div className="panel card">
          <span className="eyebrow">Worker Events</span>
          <h2>Recent queue activity</h2>
          {workerEvents.length ? (
            <div className="worker-event-list">
              {workerEvents.map((event) => (
                <div className="worker-event-item" key={`${event.worker_name}-${event.at}-${event.event_type}`}>
                  <div>
                    <strong>{event.worker_name}</strong>
                    <div className="muted">
                      {event.event_type}{event.job_id ? ` | ${event.job_id}` : ""}
                    </div>
                  </div>
                  <div className="muted">{new Date(event.at).toLocaleTimeString()}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="alert info">No worker events yet. Start both workers and queue multiple jobs.</div>
          )}
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
