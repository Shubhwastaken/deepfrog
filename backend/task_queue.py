"""
Redis Queue — Atomic Task Handling

Uses BRPOPLPUSH to atomically move jobs from job_queue → processing_queue.
This guarantees:
  - No duplicate pickup by multiple workers
  - No job loss if a worker crashes mid-processing

After successful processing, the job is removed from processing_queue.
On worker startup, any orphaned jobs in processing_queue are moved back to job_queue.
"""

import json
import logging
import redis
import os

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JOB_QUEUE = "job_queue"
PROCESSING_QUEUE = "processing_queue"


def get_redis_client():
    """Create a synchronous Redis client with a quick health check."""
    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        client.ping()
        logger.info(f"Successfully connected to Redis at {REDIS_URL}")
    except redis.exceptions.ConnectionError:
        logger.error(f"❌ CRITICAL: Could not connect to Redis at {REDIS_URL}. Ensure REDIS is running!")
    return client


def enqueue_job(job_id: str, invoice_path: str, bol_path: str, retries: int = 0):
    """Push full job payload to the job queue."""
    try:
        r = get_redis_client()
        payload = json.dumps({
            "job_id": job_id,
            "invoice_path": invoice_path,
            "bol_path": bol_path,
            "retries": retries,
        })
        r.lpush(JOB_QUEUE, payload)
        logger.info(f"Enqueued job {job_id} (retries={retries})")
    except Exception as e:
        logger.error(f"❌ Failed to enqueue job {job_id}: {e}")
        raise


def dequeue_job(timeout: int = 0):
    """
    Atomically pop a job from job_queue and push it to processing_queue.

    Uses BRPOPLPUSH for atomic move:
      job_queue (RPOP) → processing_queue (LPUSH)

    Returns parsed job dict or None on timeout.
    """
    r = get_redis_client()
    # BRPOPLPUSH: blocking right-pop from job_queue, left-push to processing_queue
    raw = r.brpoplpush(JOB_QUEUE, PROCESSING_QUEUE, timeout=timeout)
    if raw is None:
        return None
    return json.loads(raw)


def complete_job(job_id: str):
    """Remove a completed job from the processing queue."""
    r = get_redis_client()
    # Find and remove the job payload from processing_queue
    items = r.lrange(PROCESSING_QUEUE, 0, -1)
    for item in items:
        data = json.loads(item)
        if data.get("job_id") == job_id:
            r.lrem(PROCESSING_QUEUE, 1, item)
            logger.info(f"Removed job {job_id} from processing_queue")
            return
    logger.warning(f"Job {job_id} not found in processing_queue (already removed?)")


def recover_stuck_jobs(worker_id: str):
    """
    Crash recovery: On worker startup, move ALL jobs from
    processing_queue back to job_queue for re-processing.

    This handles the case where a previous worker crashed
    while processing a job, leaving it stuck in processing_queue.
    """
    r = get_redis_client()
    recovered = 0
    while True:
        # Move one item at a time from processing_queue → job_queue
        item = r.rpoplpush(PROCESSING_QUEUE, JOB_QUEUE)
        if item is None:
            break
        recovered += 1
        data = json.loads(item)
        logger.warning(
            f"[{worker_id}] Recovered stuck job {data.get('job_id')} "
            f"from processing_queue → job_queue"
        )
    if recovered > 0:
        logger.info(f"[{worker_id}] Recovered {recovered} stuck job(s) on startup")
    else:
        logger.info(f"[{worker_id}] No stuck jobs found in processing_queue")
