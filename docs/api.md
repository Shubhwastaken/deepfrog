# API Reference

Base URL: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

## Endpoints

### POST /api/auth/login
Login and receive JWT token.
```json
{ "email": "admin@customs.ai", "password": "secret" }
```

### POST /api/upload
Upload a customs document. Returns job_id.

### GET /api/results/{job_id}
Fetch processing results for a job.

### GET /health
Health check endpoint.
