# Customs Brain - Architecture

## Overview

Customs Brain is a queue-backed multi-agent system for customs document analysis. The backend handles auth, uploads, and result retrieval. Heavy document processing runs in a separate worker so production jobs are not executed inline inside the API.

## Request Flow

```text
Browser -> FastAPI backend -> Redis queue -> Worker -> Agent pipeline -> Database/report storage -> Browser
```

## Runtime Components

- `frontend`: React application for login, upload, and results review
- `backend`: FastAPI API with auth, uploads, result polling, report download, and metrics
- `worker`: async Redis consumer that executes the agent pipeline
- `postgres`: persistent relational storage for users, OTP challenges, and jobs
- `redis`: queue transport for async jobs
- `nginx`: optional edge reverse proxy
- `grafana/loki/promtail`: optional observability profile for log display

## Backend Patterns

- REST-style API routes under `backend/app/api/routes`
- singleton-style cached DB engine and session factory in `backend/app/db/session.py`
- JWT auth with password plus OTP login and refresh tokens
- role-based access control with `admin` and `general_user`
- deterministic encryption at rest for PII fields such as user emails and stored document paths
- request tracing using `request_id` and `job_id` across backend and worker logs

## Agent Pipeline

```text
ExtractionAgent
  -> HSCodeAgent
  -> WorldAgent
  -> ComplianceAgent
  -> ValuationAgent
  -> DutyAgent
  -> CriticAgent / DebateAgent
  -> MetaAgent
  -> OutputAgent
  -> ReportAgent
```

## Local Mode Caveat

`LOCAL_PIPELINE_MODE=true` now only affects local configuration defaults such as SQLite and developer-friendly auth behavior. Job execution itself no longer runs inline in the backend; uploads still require Redis plus a running worker.
