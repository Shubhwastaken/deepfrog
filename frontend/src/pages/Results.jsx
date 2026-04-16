import React, { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AppShell from "../components/AppShell";
import StatusBadge from "../components/StatusBadge";
import { downloadReport, getApiErrorMessage, getResults } from "../services/api";
import { upsertJob } from "../utils/jobs";

const SCENARIO_CONTROLS = [
  {
    key: "cost",
    label: "Duty savings",
    description: "Push lower duty and landed cost to the top of the stack.",
  },
  {
    key: "risk",
    label: "Low risk",
    description: "Favor worlds that keep customs scrutiny and downside exposure lower.",
  },
  {
    key: "confidence",
    label: "Classifier confidence",
    description: "Trust worlds with stronger HS classification certainty.",
  },
  {
    key: "compliance",
    label: "Compliance strictness",
    description: "Heavily penalize worlds that fail compliance checks.",
  },
];

const DEFAULT_SCENARIO_WEIGHTS = {
  cost: 72,
  risk: 92,
  confidence: 64,
  compliance: 100,
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

function normalizeValue(value, min, max, invert = false) {
  if (max === min) {
    return 0.5;
  }

  const normalized = (value - min) / (max - min);
  return invert ? 1 - normalized : normalized;
}

function formatCurrency(value) {
  return currencyFormatter.format(Number(value || 0));
}

function formatSignedCurrency(value) {
  if (Math.abs(value) < 0.005) {
    return "$0.00";
  }
  return `${value > 0 ? "+" : "-"}${formatCurrency(Math.abs(value))}`;
}

function formatSignedPoints(value) {
  if (Math.abs(value) < 0.005) {
    return "0.00 pts";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(2)} pts`;
}

function buildDelta(world, baseline) {
  if (!world || !baseline) {
    return null;
  }

  return {
    dutyUsd: world.estimated_duty_usd - baseline.estimated_duty_usd,
    landedCost: world.total_landed_cost_usd - baseline.total_landed_cost_usd,
    riskScore: world.risk_score - baseline.risk_score,
    confidenceScore: world.confidence_score - baseline.confidence_score,
  };
}

function buildInspectorDetails(source, fallbackReasoning = "") {
  if (!source) {
    return null;
  }

  return {
    strategy_type: source.strategy_type || "",
    assumptions: source.assumptions || [],
    required_documents: source.required_documents || [],
    risk_flags: source.risk_flags || [],
    generation_reasoning: source.generation_reasoning || fallbackReasoning || "",
    critic_citations: source.critic_citations || [],
    critic_critiques: source.critic_critiques || [],
    critic_strengths: source.critic_strengths || [],
    compliance_violations: source.compliance_violations || [],
    compliance_warnings: source.compliance_warnings || [],
    applicable_rules: source.applicable_rules || [],
    duty_calculation_breakdown: source.duty_calculation_breakdown || "",
    valuation_explanation: source.valuation_explanation || "",
    valuation_verdict: source.valuation_verdict || null,
    valuation_severity: source.valuation_severity || null,
    valuation_evidence: source.valuation_evidence || [],
  };
}

export default function Results() {
  const { jobId } = useParams();
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [scenarioWeights, setScenarioWeights] = useState(DEFAULT_SCENARIO_WEIGHTS);
  const [selectedWorldId, setSelectedWorldId] = useState(null);
  const deferredScenarioWeights = useDeferredValue(scenarioWeights);

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
  const officialWinnerId = winner ? String(winner.world_id) : null;

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

  const worldDetailsById = useMemo(() => {
    const details = new Map();

    if (winner?.world_id) {
      details.set(String(winner.world_id), buildInspectorDetails(winner, winner.reasoning));
    }

    alternatives.forEach((alternative) => {
      details.set(String(alternative.world_id), buildInspectorDetails(alternative));
    });

    return details;
  }, [alternatives, winner]);

  const scenarioWorlds = useMemo(() => {
    if (!comparisonTable.length) {
      return [];
    }

    const landedCosts = comparisonTable.map((row) => row.total_landed_cost_usd);
    const dutyValues = comparisonTable.map((row) => row.estimated_duty_usd);
    const confidenceValues = comparisonTable.map((row) => row.confidence_score);
    const riskValues = comparisonTable.map((row) => row.risk_score);
    const compositeValues = comparisonTable.map((row) => row.composite_score);
    const minLandedCost = Math.min(...landedCosts);
    const maxLandedCost = Math.max(...landedCosts);
    const minDuty = Math.min(...dutyValues);
    const maxDuty = Math.max(...dutyValues);
    const minConfidence = Math.min(...confidenceValues);
    const maxConfidence = Math.max(...confidenceValues);
    const minRisk = Math.min(...riskValues);
    const maxRisk = Math.max(...riskValues);
    const minComposite = Math.min(...compositeValues);
    const maxComposite = Math.max(...compositeValues);
    const controlWeightTotal = Object.values(deferredScenarioWeights).reduce((sum, value) => sum + value, 0);
    const baseWeight = 15;

    return comparisonTable
      .map((row, index) => {
        const worldId = String(row.world_id);
        const costEfficiency =
          (
            normalizeValue(row.total_landed_cost_usd, minLandedCost, maxLandedCost, true) +
            normalizeValue(row.estimated_duty_usd, minDuty, maxDuty, true)
          ) / 2;
        const safetyScore = normalizeValue(row.risk_score, minRisk, maxRisk, true);
        const confidenceScore = normalizeValue(row.confidence_score, minConfidence, maxConfidence);
        const complianceScore = row.is_compliant ? 1 : 0;
        const baseCompositeScore = normalizeValue(row.composite_score, minComposite, maxComposite);
        const weightedScore =
          deferredScenarioWeights.cost * costEfficiency +
          deferredScenarioWeights.risk * safetyScore +
          deferredScenarioWeights.confidence * confidenceScore +
          deferredScenarioWeights.compliance * complianceScore +
          baseCompositeScore * baseWeight;
        const scenarioScore = weightedScore / (controlWeightTotal + baseWeight);

        return {
          ...row,
          world_id: worldId,
          original_rank: index + 1,
          scenario_score: scenarioScore,
          cost_efficiency: costEfficiency,
          safety_score: safetyScore,
          compliance_score: complianceScore,
          details: worldDetailsById.get(worldId) || null,
          is_official_winner: worldId === officialWinnerId,
        };
      })
      .sort((left, right) => {
        if (right.scenario_score !== left.scenario_score) {
          return right.scenario_score - left.scenario_score;
        }
        return right.composite_score - left.composite_score;
      })
      .map((row, index) => ({
        ...row,
        scenario_rank: index + 1,
      }));
  }, [comparisonTable, deferredScenarioWeights, officialWinnerId, worldDetailsById]);

  const officialWorld = useMemo(
    () => scenarioWorlds.find((row) => row.world_id === officialWinnerId) || null,
    [officialWinnerId, scenarioWorlds]
  );
  const scenarioLeader = scenarioWorlds[0] || null;
  const rivalWorlds = useMemo(
    () => scenarioWorlds.filter((row) => row.world_id !== officialWinnerId),
    [officialWinnerId, scenarioWorlds]
  );
  const selectedWorld =
    scenarioWorlds.find((row) => row.world_id === selectedWorldId) ||
    rivalWorlds[0] ||
    officialWorld ||
    null;
  const selectedDelta = buildDelta(selectedWorld, officialWorld);

  useEffect(() => {
    if (!scenarioWorlds.length) {
      setSelectedWorldId(null);
      return;
    }

    setSelectedWorldId((currentValue) => {
      if (currentValue && scenarioWorlds.some((row) => row.world_id === currentValue)) {
        return currentValue;
      }

      const fallbackSelection =
        scenarioWorlds.find((row) => row.world_id !== officialWinnerId) ||
        scenarioWorlds[0];
      return fallbackSelection.world_id;
    });
  }, [officialWinnerId, scenarioWorlds]);

  const prioritySummary = useMemo(() => {
    const topControls = [...SCENARIO_CONTROLS]
      .sort((left, right) => deferredScenarioWeights[right.key] - deferredScenarioWeights[left.key])
      .slice(0, 2)
      .map((control) => control.label.toLowerCase());

    if (!topControls.length) {
      return "balanced priorities";
    }
    if (topControls.length === 1) {
      return topControls[0];
    }
    return `${topControls[0]} and ${topControls[1]}`;
  }, [deferredScenarioWeights]);

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
              <h2>Download and stress test</h2>
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
                  <strong>Scenario leader</strong>
                  <div>{scenarioLeader ? scenarioLeader.label : winner.label}</div>
                </div>
              </div>
              {scenarioLeader ? (
                <div className={`scenario-shift-callout ${scenarioLeader.world_id === officialWinnerId ? "steady" : "shifted"}`}>
                  <strong>{scenarioLeader.world_id === officialWinnerId ? "Official winner holds." : "Alternative pressure detected."}</strong>
                  <div>
                    {scenarioLeader.world_id === officialWinnerId
                      ? `${winner.label} still leads when you emphasize ${prioritySummary}.`
                      : `${scenarioLeader.label} jumps to #1 when you emphasize ${prioritySummary}.`}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <div className="panel card scenario-panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Scenario Lab</span>
                <h2>Re-rank worlds under pressure</h2>
                <p className="muted" style={{ marginBottom: 0 }}>
                  Move the sliders to simulate a harder cost mandate, a stricter compliance posture, or a higher
                  confidence bar. The backend winner stays official, while this lens shows what could rise under a
                  different operating brief.
                </p>
              </div>
              <button className="button ghost" onClick={() => setScenarioWeights(DEFAULT_SCENARIO_WEIGHTS)} type="button">
                Reset Lens
              </button>
            </div>
            <div className="scenario-grid">
              <div className="scenario-controls">
                {SCENARIO_CONTROLS.map((control) => (
                  <label className="priority-control" key={control.key}>
                    <div className="priority-header">
                      <div>
                        <strong>{control.label}</strong>
                        <div className="muted">{control.description}</div>
                      </div>
                      <span className="priority-value">{scenarioWeights[control.key]}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="1"
                      value={scenarioWeights[control.key]}
                      onChange={(event) => {
                        const nextValue = Number(event.target.value);
                        setScenarioWeights((currentValue) => ({
                          ...currentValue,
                          [control.key]: nextValue,
                        }));
                      }}
                    />
                  </label>
                ))}
              </div>
              <div className="scenario-side">
                <div className={`scenario-leader-card ${scenarioLeader?.world_id === officialWinnerId ? "steady" : "shifted"}`}>
                  <span className="eyebrow">Current leader</span>
                  <h3>{scenarioLeader ? scenarioLeader.label : "No worlds available"}</h3>
                  <p className="muted" style={{ marginTop: 0 }}>
                    {scenarioLeader?.world_id === officialWinnerId
                      ? `${winner.label} stays in front when ${prioritySummary} dominate the score.`
                      : `${scenarioLeader?.label} now outranks ${winner.label} because ${prioritySummary} dominate the score.`}
                  </p>
                  {scenarioLeader ? (
                    <div className="leader-metrics">
                      <div>
                        <span className="metric-label">Scenario Fit</span>
                        <strong>{Math.round(scenarioLeader.scenario_score * 100)} / 100</strong>
                      </div>
                      <div>
                        <span className="metric-label">Official Rank</span>
                        <strong>#{scenarioLeader.original_rank}</strong>
                      </div>
                      <div>
                        <span className="metric-label">Scenario Rank</span>
                        <strong>#{scenarioLeader.scenario_rank}</strong>
                      </div>
                    </div>
                  ) : null}
                </div>
                <div className="scenario-ranking">
                  {scenarioWorlds.map((world) => (
                    <button
                      className={`scenario-rank-item${selectedWorld?.world_id === world.world_id ? " active" : ""}${
                        world.is_official_winner ? " official" : ""
                      }`}
                      key={world.world_id}
                      onClick={() => setSelectedWorldId(world.world_id)}
                      type="button"
                    >
                      <div className="scenario-rank-top">
                        <div>
                          <strong>{world.label}</strong>
                          <div className="muted">
                            Rank #{world.scenario_rank} | HS {world.hs_code}
                          </div>
                        </div>
                        <span className="scenario-score">{Math.round(world.scenario_score * 100)}</span>
                      </div>
                      <div className="scenario-bar">
                        <span style={{ width: `${Math.max(8, Math.round(world.scenario_score * 100))}%` }} />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="panel card rivals-panel">
              <span className="eyebrow">Rival Cards</span>
              <h2>Challenge the official winner</h2>
              <p className="muted">
                Each rival card shows how far it drifts from the official recommendation. Click one to inspect its
                evidence and tradeoffs against the official winner.
              </p>
              {rivalWorlds.length ? (
                <div className="rival-card-list">
                  {rivalWorlds.map((world) => {
                    const delta = buildDelta(world, officialWorld);
                    const outranksOfficial = officialWorld ? world.scenario_rank < officialWorld.scenario_rank : false;

                    return (
                      <button
                        className={`rival-card${selectedWorld?.world_id === world.world_id ? " selected" : ""}${
                          outranksOfficial ? " upset" : ""
                        }`}
                        key={world.world_id}
                        onClick={() => setSelectedWorldId(world.world_id)}
                        type="button"
                      >
                        <div className="rival-card-top">
                          <div>
                            <strong>{world.label}</strong>
                            <div className="muted">
                              HS {world.hs_code} | scenario rank #{world.scenario_rank}
                            </div>
                          </div>
                          <span className="rival-score">{Math.round(world.scenario_score * 100)}</span>
                        </div>
                        <div className="delta-pill-row">
                          <span className={`delta-pill ${delta && delta.landedCost <= 0 ? "better" : "worse"}`}>
                            Landed {delta ? formatSignedCurrency(delta.landedCost) : "$0.00"}
                          </span>
                          <span className={`delta-pill ${delta && delta.riskScore <= 0 ? "better" : "worse"}`}>
                            Risk {delta ? formatSignedPoints(delta.riskScore) : "0.00 pts"}
                          </span>
                          <span className={`delta-pill ${delta && delta.confidenceScore >= 0 ? "better" : "worse"}`}>
                            Confidence {delta ? formatSignedPoints(delta.confidenceScore) : "0.00 pts"}
                          </span>
                        </div>
                        <div className="signal-strip">
                          <span className={`signal-pill ${world.is_compliant ? "good" : "danger"}`}>
                            {world.is_compliant ? "Compliant" : "Non-compliant"}
                          </span>
                          <span className="signal-pill neutral">{world.recommendation}</span>
                          {outranksOfficial ? <span className="signal-pill warning">Upsets official winner</span> : null}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="alert info">No alternative worlds were returned.</div>
              )}
              {selectedWorld ? (
                <div className="rival-inspector">
                  <span className="eyebrow">Pinned inspector</span>
                  <h3>{selectedWorld.label}</h3>
                  <p className="muted">
                    {selectedWorld.world_id === officialWinnerId
                      ? "This is the backend's official recommendation. Use the rivals to inspect where tradeoffs become tempting."
                      : selectedWorld.details?.generation_reasoning ||
                        "This rival does not ship extra generation notes, but its metric deltas are reflected throughout the chart and scenario lab."}
                  </p>
                  <div className="inspector-grid">
                    <div className="evidence-card">
                      <strong>{selectedWorld.world_id === officialWinnerId ? "Why it won" : "Why it lost"}</strong>
                      {selectedWorld.details?.critic_critiques?.length ? (
                        <ul className="evidence-list">
                          {selectedWorld.details.critic_critiques.map((critique) => (
                            <li key={critique}>{critique}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="inspector-empty">No critic critiques were returned for this world.</div>
                      )}
                    </div>
                    <div className="evidence-card">
                      <strong>Residual strengths</strong>
                      {selectedWorld.details?.critic_strengths?.length ? (
                        <ul className="evidence-list">
                          {selectedWorld.details.critic_strengths.map((strength) => (
                            <li key={strength}>{strength}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="inspector-empty">No explicit strengths were returned for this world.</div>
                      )}
                    </div>
                    <div className="evidence-card">
                      <strong>Compliance signals</strong>
                      {selectedWorld.details?.compliance_violations?.length ? (
                        <ul className="evidence-list danger">
                          {selectedWorld.details.compliance_violations.map((violation) => (
                            <li key={violation}>{violation}</li>
                          ))}
                        </ul>
                      ) : selectedWorld.details?.compliance_warnings?.length ? (
                        <ul className="evidence-list warning">
                          {selectedWorld.details.compliance_warnings.map((warning) => (
                            <li key={warning}>{warning}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="inspector-empty">No violations or warnings were returned for this world.</div>
                      )}
                      {selectedWorld.details?.applicable_rules?.length ? (
                        <div className="tag-cloud" style={{ marginTop: "12px" }}>
                          {selectedWorld.details.applicable_rules.slice(0, 6).map((rule) => (
                            <span className="tag-pill" key={rule}>{rule}</span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                    <div className="evidence-card">
                      <strong>Duty path</strong>
                      {selectedWorld.details?.duty_calculation_breakdown ? (
                        <p className="muted" style={{ marginBottom: 0 }}>
                          {selectedWorld.details.duty_calculation_breakdown}
                        </p>
                      ) : (
                        <div className="inspector-empty">No duty calculation breakdown was returned for this world.</div>
                      )}
                    </div>
                    <div className="evidence-card">
                      <strong>Valuation screen</strong>
                      {selectedWorld.details?.valuation_explanation ? (
                        <>
                          <p className="muted">
                            {selectedWorld.details.valuation_explanation}
                          </p>
                          {selectedWorld.details.valuation_evidence?.length ? (
                            <ul className="evidence-list compact">
                              {selectedWorld.details.valuation_evidence.map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          ) : null}
                        </>
                      ) : (
                        <div className="inspector-empty">No valuation evidence was returned for this world.</div>
                      )}
                    </div>
                    <div className="evidence-card">
                      <strong>Supporting citations</strong>
                      {selectedWorld.details?.critic_citations?.length ? (
                        <div className="citation-list">
                          {selectedWorld.details.critic_citations.map((citation) => (
                            <div className="citation-card" key={`${citation.title}-${citation.detail}`}>
                              <span className="metric-label">{citation.title}</span>
                              <div>{citation.detail}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="inspector-empty">No critic citations were returned for this world.</div>
                      )}
                    </div>
                  </div>
                  {selectedWorld.details?.risk_flags?.length ? (
                    <div className="inspector-group">
                      <strong>Risk flags</strong>
                      <div className="tag-cloud">
                        {selectedWorld.details.risk_flags.map((flag) => (
                          <span className="tag-pill" key={flag}>{flag}</span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {selectedWorld.details?.required_documents?.length ? (
                    <div className="inspector-group">
                      <strong>Required documents</strong>
                      <div className="tag-cloud">
                        {selectedWorld.details.required_documents.map((documentName) => (
                          <span className="tag-pill" key={documentName}>{documentName}</span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
          </div>

          <div className="grid two">
            <div className="panel card">
              <span className="eyebrow">Meta Reasoning</span>
              <h2>Why this world won</h2>
              <p className="muted" style={{ whiteSpace: "pre-wrap" }}>{output.meta_reasoning}</p>
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
                  <div className="muted">{formatCurrency(winner.total_landed_cost_usd)}</div>
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
                    <tr
                      className={`comparison-row${
                        String(row.world_id) === officialWinnerId ? " official" : ""
                      }${String(row.world_id) === selectedWorld?.world_id ? " selected" : ""}`}
                      key={row.world_id}
                    >
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
