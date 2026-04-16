"""
Process routes — POST /process and GET /status/{job_id}

POST /process:
  - Accepts invoice + BOL file uploads
  - Saves files, computes hash for idempotency
  - If duplicate → returns existing job
  - Else → creates job, enqueues to Redis

GET /status/{job_id}:
  - Returns full job status with timestamps and result
"""

import uuid
import os
import sys
import logging
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException

# Ensure backend/ is importable for queue/jobs modules
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from utils.hashing import compute_file_hash
from task_queue import enqueue_job
from jobs import create_job, get_job, get_job_by_hash

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def _save_upload(file: UploadFile, prefix: str) -> str:
    """Save an uploaded file with a UUID prefix to avoid collisions."""
    safe_name = f"{prefix}_{uuid.uuid4().hex[:8]}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, safe_name)
    async with aiofiles.open(path, "wb") as f:
        content = await file.read()
        await f.write(content)
    return os.path.abspath(path)


@router.post("/process")
async def process_documents(
    invoice: UploadFile = File(...),
    bol: UploadFile = File(...),
):
    """
    Submit invoice + BOL for async AI pipeline processing.

    Returns existing job if same files were already processed (idempotency).
    """
    # ── Step 1: Save files ──────────────────────────────────────
    invoice_path = await _save_upload(invoice, "invoice")
    bol_path = await _save_upload(bol, "bol")

    logger.info(f"Files saved: invoice={invoice_path}, bol={bol_path}")

    # ── Step 2: Compute hash for idempotency ────────────────────
    file_hash = compute_file_hash(invoice_path, bol_path)

    # ── Step 3: Check for existing job ──────────────────────────
    # Bypass idempotency in MOCK mode to allow testing code changes
    force_mock = os.getenv("FORCE_MOCK", "false").lower() == "true"
    
    if not force_mock:
        existing_job = get_job_by_hash(file_hash)
        if existing_job:
            logger.info(f"Idempotent hit: returning existing job {existing_job.id}")
            return {
                "job_id": existing_job.id,
                "status": existing_job.status,
                "message": "Duplicate submission — returning existing job",
            }

    # ── Step 4: Create new job ──────────────────────────────────
    job_id = str(uuid.uuid4())
    create_job(job_id, invoice_path, bol_path, file_hash)

    # ── Step 5: Push to Redis queue ─────────────────────────────
    enqueue_job(job_id, invoice_path, bol_path)

    logger.info(f"Job {job_id} created and enqueued")

    return {
        "job_id": job_id,
        "status": "queued",
    }


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the current status of a processing job.

    Returns status, result (if completed), and timestamps.
    """
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = {
        "job_id": job.id,
        "status": job.status,
        "result": job.result,
        "retries": job.retries,
        "timestamps": {
            "queued_at": job.queued_at.isoformat() if job.queued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        },
    }

    if job.status == "failed":
        response["error"] = job.error_message

    return response
