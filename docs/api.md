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
Upload both required shipping documents as multipart form data:
- `invoice`
- `bill_of_lading`

Returns the queued `job_id`.

### GET /api/results/{job_id}
Fetch processing results for a job, including final worker output when available.

### GET /api/results/{job_id}/report
Download the generated report file for a completed job.

## Smoke Test

Once Docker, PostgreSQL, Redis, and an LLM API key are configured, you can run a manual
end-to-end check with the bundled sample documents:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_flow.ps1
```

This will:
- check `/health`
- upload `tests/fixtures/sample_invoice.txt` and `tests/fixtures/sample_bill_of_lading.txt`
- poll `/api/results/{job_id}`
- download the generated report when the job completes

### GET /health
Health check endpoint.
