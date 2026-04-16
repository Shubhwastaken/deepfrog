import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import { downloadReport, getApiErrorMessage, getResults } from "../services/api";
import { upsertJob } from "../utils/jobs";

export default function Results() {
  const { jobId } = useParams();
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    let pollTimer;
    let cancelled = false;

    async function loadResults() {
      try {
        const response = await getResults(jobId);
        if (cancelled) return;
        setResults(response);
        setError("");
        upsertJob({
          job_id: response.job_id,
          status: response.status,
        });
        if (response.status === "queued" || response.status === "processing") {
          pollTimer = window.setTimeout(loadResults, 4000);
        }
      } catch (resultsError) {
        if (!cancelled) {
          setError(getApiErrorMessage(resultsError, "Could not load job results."));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadResults();

    return () => {
      cancelled = true;
      if (pollTimer) {
        window.clearTimeout(pollTimer);
      }
    };
  }, [jobId]);

  const output = results?.results;
  const winner = output?.winner_details;
  const alternatives = output?.alternatives || [];
  const comparisonTable = output?.comparison_table || [];
  const hasCompletedOutput = results?.status === "completed" && output && winner;

  const statusSubtitle = useMemo(() => {
    if (!results) {
      return "Loading the job state from the backend.";
    }
    if (results.status === "queued") {
      return "The shipment is queued and waiting for worker capacity.";
    }
    if (results.status === "processing") {
      return "The worker is evaluating customs worlds and polling will continue automatically.";
    }
    if (results.status === "failed") {
      return "The backend recorded a failure for this job. Review the error and re-upload if needed.";
    }
    return "The final recommendation is ready, including alternatives, reasoning, and report download.";
  }, [results]);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const blob = await downloadReport(jobId);
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `${jobId}-customs-report.md`;
      link.click();
      window.URL.revokeObjectURL(blobUrl);
    } catch (downloadError) {
      setError(getApiErrorMessage(downloadError, "Could not download the report."));
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <AppShell title={`Job ${jobId}`} subtitle={statusSubtitle}>
      {error ? <div className="alert error" style={{ marginBottom: "20px" }}>{error}</div> : null}

      <div className="hero-panel panel">
        <div className="topbar" style={{ marginBottom: 0 }}>
          <div>
            <span className="eyebrow">Job Status</span>
            <h2 style={{ marginBottom: "8px" }}>{results ? results.status : "Loading"}</h2>
            <p className="muted" style={{ margin: 0 }}>
              Source document paths are hidden from the browser. Track progress here and download the report when the job completes.
            </p>
          </div>
          <div className="button-row">
            <StatusBadge status={results?.status} />
            <Link className="button secondary" to="/upload">
              New Upload
            </Link>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="panel card" style={{ display: "flex", gap: "18px", alignItems: "center" }}>
          <div className="spinner" />
          <div>
            <h2 style={{ marginBottom: "6px" }}>Loading results</h2>
            <p className="muted" style={{ margin: 0 }}>
              Waiting for the backend to respond with the latest job state.
            </p>
          </div>
        </div>
      ) : null}

      {!isLoading && (results?.status === "queued" || results?.status === "processing") ? (
        <div className="panel card">
          <h2>Pipeline in progress</h2>
          <p className="muted">
            This page polls automatically every few seconds. Leave it open or come back later from the dashboard.
          </p>
        </div>
      ) : null}

      {!isLoading && results?.status === "failed" ? (
        <div className="panel card">
          <h2>Job failed</h2>
          <div className="alert error">{results.error_message || "No error details were returned by the backend."}</div>
        </div>
      ) : null}

      {hasCompletedOutput ? (
        <div className="results-layout">
          <div className="summary-grid">
            <div className="panel card">
              <span className="eyebrow">Recommended World</span>
              <h2>{winner.label}</h2>
              <p className="muted">{output.plain_language_summary}</p>
              <div className="metric-row">
                <div className="metric">
                  <span className="metric-label">HS Code</span>
                  <div className="metric-value">{winner.hs_code}</div>
                </div>
                <div className="metric">
                  <span className="metric-label">Duty Rate</span>
                  <div className="metric-value">{winner.duty_rate_percent.toFixed(2)}%</div>
                </div>
                <div className="metric">
                  <span className="metric-label">Duty USD</span>
                  <div className="metric-value">${winner.estimated_duty_usd.toFixed(2)}</div>
                </div>
                <div className="metric">
                  <span className="metric-label">Risk Score</span>
                  <div className="metric-value">{winner.risk_score.toFixed(2)}</div>
                </div>
              </div>
            </div>

            <div className="panel card">
              <span className="eyebrow">Actions</span>
              <h2>Download and compare</h2>
              <div className="button-row">
                <button className="button primary" disabled={isDownloading} onClick={handleDownload} type="button">
                  {isDownloading ? "Downloading..." : "Download Report"}
                </button>
              </div>
              <div className="field-grid" style={{ marginTop: "18px" }}>
                <div className="alert info">
                  <strong>Destination</strong>
                  <div>{winner.destination_country || "Unknown"}</div>
                </div>
                <div className="alert info">
                  <strong>Recommendation</strong>
                  <div>{winner.recommendation}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="panel card">
            <span className="eyebrow">Meta Reasoning</span>
            <h2>Why this world won</h2>
            <p className="muted" style={{ whiteSpace: "pre-wrap" }}>{output.meta_reasoning}</p>
          </div>

          <div className="grid two">
            <div className="panel card">
              <span className="eyebrow">Alternatives</span>
              <h2>Other ranked worlds</h2>
              {alternatives.length ? (
                <ul className="list">
                  {alternatives.map((alternative) => (
                    <li key={alternative.world_id}>
                      <strong>{alternative.label}</strong>
                      <div className="muted">
                        HS {alternative.hs_code} | score {alternative.composite_score.toFixed(2)} | {alternative.recommendation}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="alert info">No alternative worlds were returned.</div>
              )}
            </div>

            <div className="panel card">
              <span className="eyebrow">Winner Detail</span>
              <h2>Operational snapshot</h2>
              <ul className="list">
                <li>
                  <strong>Product</strong>
                  <div className="muted">{winner.product_description}</div>
                </li>
                <li>
                  <strong>Landed Cost</strong>
                  <div className="muted">${winner.total_landed_cost_usd.toFixed(2)}</div>
                </li>
                <li>
                  <strong>Compliance Status</strong>
                  <div className="muted">{winner.is_compliant ? "Compliant" : "Non-compliant"}</div>
                </li>
              </ul>
            </div>
          </div>

          <div className="panel card">
            <span className="eyebrow">World Comparison</span>
            <h2>Comparison table</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>World</th>
                    <th>HS Code</th>
                    <th>Confidence</th>
                    <th>Compliant</th>
                    <th>Duty Rate</th>
                    <th>Duty USD</th>
                    <th>Landed Cost</th>
                    <th>Risk</th>
                    <th>Recommendation</th>
                    <th>Composite</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonTable.map((row) => (
                    <tr key={row.world_id}>
                      <td>{row.label}</td>
                      <td>{row.hs_code}</td>
                      <td>{row.confidence_score.toFixed(2)}</td>
                      <td>{row.is_compliant ? "Yes" : "No"}</td>
                      <td>{row.duty_rate_percent.toFixed(2)}%</td>
                      <td>${row.estimated_duty_usd.toFixed(2)}</td>
                      <td>${row.total_landed_cost_usd.toFixed(2)}</td>
                      <td>{row.risk_score.toFixed(2)}</td>
                      <td>{row.recommendation}</td>
                      <td>{row.composite_score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
