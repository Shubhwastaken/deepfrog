import React, { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { beginLogin, isAuthenticated, verifyOtp } from "../services/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [challenge, setChallenge] = useState(null);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  if (isAuthenticated()) {
    return <Navigate replace to="/dashboard" />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setInfoMessage("");
    setIsSubmitting(true);
    try {
      if (!challenge) {
        const response = await beginLogin(email, password);
        setChallenge(response);
        setInfoMessage(
          response.delivery_channel === "email"
            ? `A one-time code was sent to ${response.masked_destination}.`
            : `Enter the one-time code for ${response.masked_destination}.`
        );
      } else {
        await verifyOtp(challenge.challenge_id, otpCode);
        navigate(location.state?.from || "/dashboard", { replace: true });
      }
    } catch (submitError) {
      setError(submitError?.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="panel login-panel">
        <div className="login-showcase">
          <span className="eyebrow">Agentic Customs Intelligence</span>
          <h1 className="brand-title">Choose the safest world before customs chooses for you.</h1>
          <p className="brand-subtitle" style={{ color: "rgba(255,255,255,0.82)" }}>
            Customs Brain compares multiple HS classification worlds, tests each one for compliance,
            estimates landed cost, and gives your team a report-ready recommendation.
          </p>
          <div className="login-stats">
            <div className="login-stat">
              <strong>1. Upload both source documents</strong>
              <p className="muted" style={{ color: "rgba(255,255,255,0.8)", marginBottom: 0 }}>
                Invoice and bill of lading are processed together for a single customs job.
              </p>
            </div>
            <div className="login-stat">
              <strong>2. Compare alternative worlds</strong>
              <p className="muted" style={{ color: "rgba(255,255,255,0.8)", marginBottom: 0 }}>
                Each world gets scored on compliance, landed cost, and classification risk.
              </p>
            </div>
            <div className="login-stat">
              <strong>3. Download the report</strong>
              <p className="muted" style={{ color: "rgba(255,255,255,0.8)", marginBottom: 0 }}>
                Share the final recommendation, alternatives, and reasoning with operations teams.
              </p>
            </div>
          </div>
        </div>
        <div className="login-form">
          <span className="eyebrow">Secure Entry</span>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "34px", marginTop: "10px" }}>
            Sign in to review jobs
          </h2>
          <p className="muted">
            Passwords are stored as secure hashes, and sign-in completes with a one-time verification code.
          </p>
          <form className="field-grid" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                autoComplete="username"
                placeholder="you@company.com"
                disabled={Boolean(challenge)}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            {!challenge ? (
              <div className="field">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </div>
            ) : (
              <div className="field">
                <label htmlFor="otp-code">One-Time Code</label>
                <input
                  id="otp-code"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  placeholder="6-digit code"
                  value={otpCode}
                  onChange={(event) => setOtpCode(event.target.value)}
                />
              </div>
            )}
            {infoMessage ? <div className="alert info">{infoMessage}</div> : null}
            {challenge?.debug_otp ? (
              <div className="alert info">
                Development OTP: <span className="code">{challenge.debug_otp}</span>
              </div>
            ) : null}
            {error ? <div className="alert error">{error}</div> : null}
            <div className="button-row">
              <button className="button primary" disabled={isSubmitting} type="submit">
                {isSubmitting ? "Signing In..." : challenge ? "Verify And Enter" : "Send OTP Code"}
              </button>
              {challenge ? (
                <button
                  className="button secondary"
                  onClick={() => {
                    setChallenge(null);
                    setOtpCode("");
                    setInfoMessage("");
                    setError("");
                  }}
                  type="button"
                >
                  Start Over
                </button>
              ) : null}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
