# Setup Guide

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (local frontend dev)
- Python 3.11+ (local backend dev)

## Quick Start (Docker)
```bash
cp .env.example .env
# Edit .env and add your API keys
docker-compose up --build
```

## Access
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Local Development

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn --app-dir backend app.main:app --reload
```

### Worker
```bash
python -m workers.worker
```

The worker is mandatory for local uploads now. The backend no longer runs jobs inline.

### Two Local Workers
```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_two_workers.ps1
```

This starts `worker-a` and `worker-b`, which both pull from the same Redis queue.

### Frontend
```bash
cd frontend
npm install
npm start
```

## Environment Variables
| Variable | Description |
|---|---|
| DATABASE_URL | PostgreSQL connection |
| REDIS_URL | Redis connection |
| SECRET_KEY | JWT signing secret |
| ANTHROPIC_API_KEY | Anthropic API key |
| OPENAI_API_KEY | OpenAI API key (optional) |
