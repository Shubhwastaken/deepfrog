import React, { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { beginLogin, getAuthProviders, isAuthenticated, loginWithGoogle, verifyOtp } from "../services/auth";

const GOOGLE_IDENTITY_SCRIPT = "https://accounts.google.com/gsi/client";

const loadGoogleIdentityScript = () => (
  new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[src="${GOOGLE_IDENTITY_SCRIPT}"]`);
    if (existingScript) {
      if (window.google?.accounts?.id) {
        resolve();
        return;
      }
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("Failed to load Google Sign-In.")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.src = GOOGLE_IDENTITY_SCRIPT;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Sign-In."));
    document.head.appendChild(script);
  })
);

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [challenge, setChallenge] = useState(null);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [providerConfig, setProviderConfig] = useState(null);
  const [providerError, setProviderError] = useState("");
  const googleButtonRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  if (isAuthenticated()) {
    return <Navigate replace to="/dashboard" />;
  }

  useEffect(() => {
    let isMounted = true;

    const loadProviders = async () => {
      try {
        const providers = await getAuthProviders();
        if (isMounted) {
          setProviderConfig(providers);
        }
      } catch (loadError) {
        if (isMounted) {
          setProviderError(loadError?.response?.data?.detail || "Unable to load sign-in providers.");
        }
      }
    };

    loadProviders();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const googleProvider = providerConfig?.google;
    if (!googleProvider?.enabled || !googleProvider?.client_id || challenge || !googleButtonRef.current) {
      return undefined;
    }

    let isCancelled = false;

    const setupGoogleButton = async () => {
      try {
        await loadGoogleIdentityScript();
        if (isCancelled || !window.google?.accounts?.id || !googleButtonRef.current) {
          return;
        }

        googleButtonRef.current.innerHTML = "";
        window.google.accounts.id.initialize({
          client_id: googleProvider.client_id,
          callback: async ({ credential }) => {
            if (!credential) {
              setError("Google did not return a credential. Please try again.");
              return;
            }

            setError("");
            setInfoMessage("");
            setIsSubmitting(true);
            try {
              await loginWithGoogle(credential);
              navigate(location.state?.from || "/dashboard", { replace: true });
            } catch (googleError) {
              setError(googleError?.response?.data?.detail || "Google Sign-In failed. Please try again.");
            } finally {
              setIsSubmitting(false);
            }
          },
        });

        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          text: "signin_with",
          shape: "pill",
          width: Math.max(280, Math.min(420, googleButtonRef.current.offsetWidth || 360)),
        });
      } catch (scriptError) {
        if (!isCancelled) {
          setProviderError(scriptError.message);
        }
      }
    };

    setupGoogleButton();

    return () => {
      isCancelled = true;
    };
  }, [challenge, location.state, navigate, providerConfig]);

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
          <div className="login-signal-row">
            <span className="signal-pill good">Encrypted PII</span>
            <span className="signal-pill neutral">JWT Sessions</span>
            <span className="signal-pill warning">2 Worker Pipeline</span>
          </div>
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
          {!challenge && providerConfig?.google?.enabled ? (
            <div className="login-provider-stack">
              <div className="google-auth-card">
                <div>
                  <strong>Google Sign-In</strong>
                  <p className="muted" style={{ marginBottom: 0 }}>
                    Use your verified Google account for direct access, then the app issues its own JWT session.
                  </p>
                </div>
                <div className="google-button-shell" ref={googleButtonRef} />
              </div>
              <div className="login-divider">
                <span>or use password + OTP</span>
              </div>
            </div>
          ) : null}
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
            {providerError ? <div className="alert error">{providerError}</div> : null}
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
