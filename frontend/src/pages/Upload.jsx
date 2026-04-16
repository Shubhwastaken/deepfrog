import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import AppShell from "../components/AppShell";
import { getApiErrorMessage, uploadDocuments } from "../services/api";
import { upsertJob } from "../utils/jobs";

export default function Upload() {
  const navigate = useNavigate();
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [billOfLadingFile, setBillOfLadingFile] = useState(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleUpload = async () => {
    if (!invoiceFile || !billOfLadingFile) {
      setError("Both the invoice and bill of lading files are required.");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const response = await uploadDocuments({ invoiceFile, billOfLadingFile });
      upsertJob({
        job_id: response.job_id,
        status: response.status,
      });
      navigate(`/results/${response.job_id}`);
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Upload failed. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell
      title="New Shipment Review"
      subtitle="Upload both documents for a single customs job. The backend will queue the worker pipeline and the results page will start polling automatically."
    >
      <div className="grid two">
        <div className="panel card">
          <span className="eyebrow">Documents</span>
          <h2>Required source files</h2>
          <div className="field-grid">
            <div className="upload-box">
              <div className="field">
                <label htmlFor="invoice-upload">Invoice</label>
                <input
                  id="invoice-upload"
                  type="file"
                  onChange={(event) => setInvoiceFile(event.target.files?.[0] || null)}
                />
              </div>
              <div className="upload-meta">
                <span>{invoiceFile ? invoiceFile.name : "No invoice selected"}</span>
                <span>{invoiceFile ? `${Math.ceil(invoiceFile.size / 1024)} KB` : "PDF or text"}</span>
              </div>
            </div>

            <div className="upload-box">
              <div className="field">
                <label htmlFor="bol-upload">Bill of Lading</label>
                <input
                  id="bol-upload"
                  type="file"
                  onChange={(event) => setBillOfLadingFile(event.target.files?.[0] || null)}
                />
              </div>
              <div className="upload-meta">
                <span>{billOfLadingFile ? billOfLadingFile.name : "No bill of lading selected"}</span>
                <span>{billOfLadingFile ? `${Math.ceil(billOfLadingFile.size / 1024)} KB` : "PDF or text"}</span>
              </div>
            </div>
          </div>

          {error ? <div className="alert error" style={{ marginTop: "18px" }}>{error}</div> : null}

          <div className="button-row" style={{ marginTop: "20px" }}>
            <button className="button primary" disabled={isSubmitting} onClick={handleUpload} type="button">
              {isSubmitting ? "Submitting..." : "Create Customs Job"}
            </button>
          </div>
        </div>

        <div className="panel card">
          <span className="eyebrow">Pipeline</span>
          <h2>What happens after upload</h2>
          <ul className="list">
            <li>Extraction agent reconciles the invoice and bill of lading into a structured shipment view.</li>
            <li>HS code and world agents generate multiple customs interpretations.</li>
            <li>Compliance, duty, and debate agents test each world for risk, cost, and rule alignment.</li>
            <li>Meta and output agents select the strongest world and prepare a report-ready result object.</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
