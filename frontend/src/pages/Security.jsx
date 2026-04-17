import React, { useEffect, useState } from "react";

import AppShell from "../components/AppShell";
import { getSecurityStorageProof } from "../services/api";

function SecurityMetric({ label, value }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <div className="metric-value">{value}</div>
    </div>
  );
}

export default function Security() {
  const [proof, setProof] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadProof() {
      try {
        const response = await getSecurityStorageProof();
        if (!cancelled) {
          setProof(response);
          setError("");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError?.response?.data?.detail || "Could not load database security proof.");
        }
      }
    }

    loadProof();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell
      title="Security Proof"
      subtitle="Admin-only storage proof showing that sensitive database fields are encrypted at rest and login secrets are hashed before judges or auditors inspect the system."
    >
      <div className="panel hero-panel">
        <div className="signal-strip">
          <span className="signal-pill good">Encrypted At Rest</span>
          <span className="signal-pill neutral">Prefix {proof?.encryption_prefix || "enc::"}</span>
          <span className="signal-pill warning">Passwords Are Hashed</span>
        </div>
        <p className="muted" style={{ marginTop: "16px", marginBottom: 0 }}>
          This page reads raw PostgreSQL values through an admin-only API path. It shows encrypted samples as they
          exist in the database, not the decrypted values used by the normal app screens.
        </p>
      </div>

      {error ? <div className="alert error">{error}</div> : null}

      <div className="grid two">
        <div className="panel card">
          <span className="eyebrow">Users Table</span>
          <h2>User storage proof</h2>
          <div className="metric-row">
            <SecurityMetric label="Total Users" value={proof?.user_summary?.total_users ?? "--"} />
            <SecurityMetric label="Encrypted Emails" value={proof?.user_summary?.encrypted_email_rows ?? "--"} />
            <SecurityMetric
              label="Encrypted Google IDs"
              value={proof?.user_summary?.encrypted_google_subject_rows ?? "--"}
            />
            <SecurityMetric label="Hashed Passwords" value={proof?.user_summary?.hashed_password_rows ?? "--"} />
          </div>
          <div className="db-proof-list">
            {(proof?.user_samples || []).map((sample) => (
              <div className="db-proof-item" key={sample.id}>
                <div className="db-proof-top">
                  <strong>{sample.id}</strong>
                  <span className={`signal-pill ${sample.email_encrypted ? "good" : "danger"}`}>
                    Email {sample.email_encrypted ? "Encrypted" : "Plain"}
                  </span>
                </div>
                <div className="db-proof-grid">
                  <div>
                    <span className="metric-label">Email Prefix</span>
                    <code className="db-proof-code">{sample.email_prefix || "n/a"}</code>
                  </div>
                  <div>
                    <span className="metric-label">Google Subject Prefix</span>
                    <code className="db-proof-code">{sample.google_subject_prefix || "n/a"}</code>
                  </div>
                  <div>
                    <span className="metric-label">Password Hash Prefix</span>
                    <code className="db-proof-code">{sample.password_hash_prefix || "n/a"}</code>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel card">
          <span className="eyebrow">Jobs Table</span>
          <h2>Pipeline storage proof</h2>
          <div className="metric-row security-metrics">
            <SecurityMetric label="Total Jobs" value={proof?.job_summary?.total_jobs ?? "--"} />
            <SecurityMetric label="Owner Emails" value={proof?.job_summary?.encrypted_owner_email_rows ?? "--"} />
            <SecurityMetric label="Doc Paths" value={proof?.job_summary?.encrypted_invoice_path_rows ?? "--"} />
            <SecurityMetric label="Reports" value={proof?.job_summary?.encrypted_report_path_rows ?? "--"} />
            <SecurityMetric label="Results Blob" value={proof?.job_summary?.encrypted_results_rows ?? "--"} />
          </div>
          <div className="db-proof-list">
            {(proof?.job_samples || []).map((sample) => (
              <div className="db-proof-item" key={sample.id}>
                <div className="db-proof-top">
                  <strong>{sample.id}</strong>
                  <span className={`signal-pill ${sample.results_encrypted ? "good" : "danger"}`}>
                    Results {sample.results_encrypted ? "Encrypted" : "Plain"}
                  </span>
                </div>
                <div className="db-proof-grid">
                  <div>
                    <span className="metric-label">Owner Email</span>
                    <code className="db-proof-code">{sample.owner_email_prefix || "n/a"}</code>
                  </div>
                  <div>
                    <span className="metric-label">Invoice Path</span>
                    <code className="db-proof-code">{sample.invoice_path_prefix || "n/a"}</code>
                  </div>
                  <div>
                    <span className="metric-label">Bill Of Lading Path</span>
                    <code className="db-proof-code">{sample.bill_path_prefix || "n/a"}</code>
                  </div>
                  <div>
                    <span className="metric-label">Report Path</span>
                    <code className="db-proof-code">{sample.report_path_prefix || "n/a"}</code>
                  </div>
                  <div className="db-proof-span-two">
                    <span className="metric-label">Encrypted Results Blob Prefix</span>
                    <code className="db-proof-code">{sample.results_prefix || "n/a"}</code>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
