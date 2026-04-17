from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, metrics, report, results, security, upload
from app.db.auth_migrations import ensure_auth_schema
from app.db.models import Base
from app.db.sensitive_migrations import migrate_sensitive_storage
from app.db.session import get_engine
from app.services.auth_service import ensure_default_user
from shared.utils.logger import configure_logging, get_logger
from shared.utils.request_context import clear_request_context, set_job_id, set_request_id

configure_logging()
logger = get_logger("customs_brain.api")

app = FastAPI(title="Customs Brain API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(results.router, prefix="/api", tags=["results"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(security.router, prefix="/api", tags=["security"])


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)
    set_job_id("-")
    started_at = time.perf_counter()
    logger.info("Request started method=%s path=%s", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001
        logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
        clear_request_context()
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request finished method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    clear_request_context()
    return response


@app.on_event("startup")
async def startup() -> None:
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await ensure_auth_schema(get_engine())
    await migrate_sensitive_storage(get_engine())
    await ensure_default_user()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
