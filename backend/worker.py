"""
Worker — Background job processor with crash recovery.

Features:
  - BRPOPLPUSH atomic task pickup (no duplicate processing)
  - Crash recovery on startup (orphaned jobs re-queued)
  - Retry logic (max 2 retries before marking failed)
  - Multi-worker support via WORKER_ID env var
  - Structured logging with worker_id + job_id

Usage:
  WORKER_ID=worker-1 python -m backend.worker
  WORKER_ID=worker-2 python -m backend.worker
"""

import os
import sys
import logging
import traceback
from datetime import datetime

# ── Setup paths ─────────────────────────────────────────────────
# Ensure backend/ and project root are importable
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_backend_dir)

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from task_queue import enqueue_job, dequeue_job, complete_job, recover_stuck_jobs
from jobs import update_job_status, save_job_result, increment_retry, mark_failed
from pipeline_wrapper import run_pipeline, PipelineError
from app.db.models import Base
from app.db.session import sync_engine

# ── Configuration ───────────────────────────────────────────────
WORKER_ID = os.getenv("WORKER_ID", "worker-1")
MAX_RETRIES = 2

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format=f"[%(asctime)s] [%(levelname)s] [{WORKER_ID}] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def ensure_tables():
    """Create database tables if they don't exist."""
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables verified")


def process_job(job_data: dict):
    """
    Process a single job from the queue.

    Flow:
      1. Update status → processing
      2. Run AI pipeline
      3. On success → save result, remove from processing_queue
      4. On failure → retry or mark failed
    """
    job_id = job_data["job_id"]
    invoice_path = job_data["invoice_path"]
    bol_path = job_data["bol_path"]
    retries = job_data.get("retries", 0)

    logger.info(f"Processing job {job_id} (attempt {retries + 1}/{MAX_RETRIES + 1})")

    # ── Step 1: Mark as processing ──────────────────────────────
    update_job_status(job_id, "processing", started_at=datetime.utcnow())

    try:
        # ── Step 2: Run pipeline ────────────────────────────────
        result = run_pipeline(invoice_path, bol_path)

        # ── Step 3: Save result ─────────────────────────────────
        save_job_result(job_id, result)
        complete_job(job_id)
        logger.info(f"Job {job_id} completed successfully ✓")

    except (PipelineError, Exception) as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        logger.debug(traceback.format_exc())

        # ── Step 4: Retry or fail ───────────────────────────────
        new_retries = increment_retry(job_id)

        if new_retries < MAX_RETRIES:
            logger.warning(f"Job {job_id} re-queued (retry {new_retries + 1}/{MAX_RETRIES})")
            update_job_status(job_id, "queued")
            # Remove from processing queue and re-enqueue
            complete_job(job_id)
            enqueue_job(job_id, invoice_path, bol_path, retries=new_retries)
        else:
            logger.error(f"Job {job_id} permanently FAILED after {MAX_RETRIES} retries")
            mark_failed(job_id, error_msg)
            complete_job(job_id)


def main():
    """Worker main loop."""
    logger.info("=" * 60)
    logger.info(f"Worker {WORKER_ID} starting...")
    logger.info("=" * 60)

    # ── Ensure DB tables exist ──────────────────────────────────
    ensure_tables()

    # ── Crash recovery ──────────────────────────────────────────
    logger.info("Running crash recovery check...")
    recover_stuck_jobs(WORKER_ID)

    # ── Main loop ───────────────────────────────────────────────
    logger.info("Waiting for jobs...")

    while True:
        try:
            # Blocking pop with 5-second timeout (allows graceful shutdown)
            job_data = dequeue_job(timeout=5)

            if job_data is None:
                continue  # Timeout, loop again

            process_job(job_data)

        except KeyboardInterrupt:
            logger.info(f"Worker {WORKER_ID} shutting down gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected worker error: {e}")
            logger.debug(traceback.format_exc())
            continue

    logger.info(f"Worker {WORKER_ID} stopped.")


if __name__ == "__main__":
    main()
