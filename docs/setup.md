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
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Worker
```bash
python -m workers.worker
```

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
