# Customs Brain

Customs Brain is a multi-agent customs classification and landed-cost analysis platform. Users upload an invoice and bill of lading, the backend fans the work out through a queue-backed worker pipeline, and the UI returns a ranked recommendation with alternatives, evidence, and a downloadable report.

## Problem Statement

Trade teams usually make customs decisions with incomplete context spread across invoices, shipping docs, tariff rules, valuation heuristics, and compliance requirements. That creates slow reviews, inconsistent HS classification choices, and avoidable landed-cost risk.

## Solution

This project turns one shipment into multiple classification worlds, evaluates each world for compliance, valuation, duty impact, and critic risk, then ranks the options and publishes a report-ready result. The platform includes:

- password login plus OTP-based MFA
- optional Google Sign-In using Google Identity Services ID tokens
- JWT access and refresh tokens
- admin versus general-user RBAC
- encrypted PII at rest for user emails and job document paths
- request/job tracing that follows backend requests into worker jobs
- structured logs written to both stdout and shared log files
- two queue consumers (`worker-a` and `worker-b`) so parallel processing is visible on the dashboard

## Tech Stack

- Frontend: React, Axios, React Router
- API: FastAPI
- Worker: Python async worker consuming Redis queue messages
- Queue: Redis
- Database: PostgreSQL in Docker, SQLite for local pipeline mode
- AI pipeline: custom agent graph under `agents/`
- Infra: Docker Compose, Nginx, optional Grafana/Loki/Promtail profile

## How To Run

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY`, `SECRET_KEY`, and `PII_ENCRYPTION_KEY`.
3. Optionally set `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
4. Optionally set `GENERAL_USER_EMAIL` and `GENERAL_USER_PASSWORD` to seed a non-admin user.
5. To enable Google Sign-In, set `GOOGLE_CLIENT_ID` and optionally `GOOGLE_ALLOWED_DOMAIN`.
6. Start the stack:

```bash
docker compose up --build
```

6. Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Even with `LOCAL_PIPELINE_MODE=true`, uploads now run only through the queue-backed flow. For local work, keep both Redis and the worker running.

## Observability

Structured logs include `service`, `request_id`, and `job_id`. To boot the optional log-display stack:

```bash
docker compose --profile observability up -d loki promtail grafana
```

Grafana will come up on `http://localhost:3001` with Loki pre-provisioned as a datasource.

## Project Structure

- `frontend/`: React application
- `backend/app/`: FastAPI routes, auth, storage, and DB access
- `workers/`: async queue worker and task router
- `agents/`: extraction, classification, compliance, duty, meta, output, and report agents
- `shared/`: shared schemas, config helpers, and logging utilities
- `infra/`: nginx and observability configuration
- `docs/`: architecture and supporting documentation

## Screens

- Login with password plus OTP
- Upload dashboard
- Ranked result view with winner, alternatives, and report download

## More Docs

- Architecture: `docs/architecture.md`
- Agents: `docs/agents.md`
- API notes: `docs/api.md`
