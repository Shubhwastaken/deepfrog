"""Redis-backed worker entrypoint for queued customs jobs."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from dataclasses import dataclass
from typing import Any, TypeVar
from typing import Awaitable, cast

import redis.asyncio as aioredis

from shared.utils.logger import get_logger
from shared.utils.request_context import clear_request_context, set_job_id, set_request_id
from shared.utils.worker_runtime import (
    WORKER_EVENT_LIMIT,
    WORKER_EVENTS_KEY,
    WORKER_HEARTBEAT_KEY,
    utcnow_iso,
)
from workers.job_store import update_job_completed, update_job_failed, update_job_processing
from workers.queue.task_router import route_task

logger = get_logger("customs_brain.worker")
RedisResultT = TypeVar("RedisResultT")


async def _resolve_redis_call(result: Awaitable[RedisResultT] | RedisResultT) -> RedisResultT:
    """Normalize redis-py calls whose type stubs return sync-or-async unions."""

    if inspect.isawaitable(result):
        return await cast(Awaitable[RedisResultT], result)
    return cast(RedisResultT, result)


async def _close_redis_client(redis_client: aioredis.Redis | None) -> None:
    """Close Redis clients across redis-py versions."""

    if redis_client is None:
        return

    close_method = getattr(redis_client, "aclose", None)
    if close_method is not None:
        await close_method()
        return

    await _resolve_redis_call(redis_client.close())


async def _hdel_fields(redis_client: aioredis.Redis, name: str, fields: list[str]) -> int:
    """Delete Redis hash fields while sidestepping inaccurate async type stubs."""

    raw_client = cast(Any, redis_client)
    return await _resolve_redis_call(raw_client.hdel(name, *fields))


@dataclass
class WorkerRuntimeState:
    worker_name: str
    service_name: str
    pid: int
    current_job_id: str | None = None
    jobs_completed: int = 0
    jobs_failed: int = 0


async def process_job_payload(
    job_payload: dict,
    *,
    registry_client: aioredis.Redis | None = None,
    runtime_state: WorkerRuntimeState | None = None,
) -> None:
    """Validate a queue payload and run the pipeline for that job."""

    job_id = job_payload.get("job_id")
    if not job_id:
        raise ValueError("Queue payload missing required job_id.")
    set_request_id(job_payload.get("request_id"))
    set_job_id(job_id)
    if runtime_state is not None:
        runtime_state.current_job_id = job_id
        await _publish_worker_snapshot(registry_client, runtime_state)
        await _publish_worker_event(registry_client, runtime_state, event_type="picked", job_id=job_id)

    try:
        document_paths = job_payload.get("document_paths")
        if not isinstance(document_paths, dict):
            await update_job_failed(job_id, "Queue payload missing valid document_paths.")
            if runtime_state is not None:
                runtime_state.jobs_failed += 1
                await _publish_worker_event(
                    registry_client,
                    runtime_state,
                    event_type="failed",
                    job_id=job_id,
                    detail="invalid document_paths shape",
                )
            return

        invoice_path = document_paths.get("invoice")
        bill_of_lading_path = document_paths.get("bill_of_lading")
        if not invoice_path or not bill_of_lading_path:
            await update_job_failed(job_id, "Queue payload missing valid document_paths.")
            if runtime_state is not None:
                runtime_state.jobs_failed += 1
                await _publish_worker_event(
                    registry_client,
                    runtime_state,
                    event_type="failed",
                    job_id=job_id,
                    detail="missing invoice or bill_of_lading path",
                )
            return

        await update_job_processing(job_id)
        logger.info("Worker picked queued job")
        try:
            result = await route_task(job_id, document_paths)
            await update_job_completed(job_id, result)
            if runtime_state is not None:
                runtime_state.jobs_completed += 1
                await _publish_worker_event(registry_client, runtime_state, event_type="completed", job_id=job_id)
            logger.info("Worker completed queued job")
        except Exception as exc:  # noqa: BLE001
            await update_job_failed(job_id, str(exc))
            if runtime_state is not None:
                runtime_state.jobs_failed += 1
                await _publish_worker_event(
                    registry_client,
                    runtime_state,
                    event_type="failed",
                    job_id=job_id,
                    detail=str(exc),
                )
            logger.exception("Worker failed to process job")
    finally:
        if runtime_state is not None:
            runtime_state.current_job_id = None
            await _publish_worker_snapshot(registry_client, runtime_state)
        clear_request_context()


async def main() -> None:
    """Consume queued jobs from Redis forever."""

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    worker_name = os.getenv("WORKER_NAME") or os.getenv("SERVICE_NAME") or f"worker-{os.getpid()}"
    service_name = os.getenv("SERVICE_NAME", "worker")
    runtime_state = WorkerRuntimeState(worker_name=worker_name, service_name=service_name, pid=os.getpid())

    logger.info("Worker %s started and waiting for jobs", worker_name)
    redis_client = await aioredis.from_url(redis_url)
    registry_client = await aioredis.from_url(redis_url)
    await _publish_worker_snapshot(registry_client, runtime_state)
    await _publish_worker_event(registry_client, runtime_state, event_type="started")
    heartbeat_task = asyncio.create_task(_heartbeat_loop(registry_client, runtime_state))

    try:
        while True:
            blpop_call = cast(Awaitable[list[bytes | str] | None], redis_client.blpop(["job_queue"]))
            queue_entry = await blpop_call
            if not queue_entry or len(queue_entry) != 2:
                logger.warning("Worker received an empty Redis queue response")
                continue

            raw_payload = queue_entry[1]
            payload_text = raw_payload.decode("utf-8") if isinstance(raw_payload, bytes) else raw_payload
            await process_job_payload(
                json.loads(payload_text),
                registry_client=registry_client,
                runtime_state=runtime_state,
            )
    finally:
        heartbeat_task.cancel()
        runtime_state.current_job_id = None
        await _publish_worker_event(registry_client, runtime_state, event_type="stopped")
        worker_fields: list[str] = [runtime_state.worker_name]
        await _hdel_fields(registry_client, WORKER_HEARTBEAT_KEY, worker_fields)
        await _close_redis_client(registry_client)
        await _close_redis_client(redis_client)


async def _heartbeat_loop(registry_client: aioredis.Redis, runtime_state: WorkerRuntimeState) -> None:
    while True:
        await _publish_worker_snapshot(registry_client, runtime_state)
        await asyncio.sleep(5)


async def _publish_worker_snapshot(
    registry_client: aioredis.Redis | None,
    runtime_state: WorkerRuntimeState,
) -> None:
    if registry_client is None:
        return

    payload = json.dumps(
        {
            "worker_name": runtime_state.worker_name,
            "service_name": runtime_state.service_name,
            "pid": runtime_state.pid,
            "current_job_id": runtime_state.current_job_id,
            "jobs_completed": runtime_state.jobs_completed,
            "jobs_failed": runtime_state.jobs_failed,
            "last_seen_at": utcnow_iso(),
        }
    )
    await _resolve_redis_call(
        registry_client.hset(
            name=WORKER_HEARTBEAT_KEY,
            key=runtime_state.worker_name,
            value=payload,
        )
    )


async def _publish_worker_event(
    registry_client: aioredis.Redis | None,
    runtime_state: WorkerRuntimeState,
    *,
    event_type: str,
    job_id: str | None = None,
    detail: str | None = None,
) -> None:
    if registry_client is None:
        return

    event_payload: dict[str, Any] = {
        "worker_name": runtime_state.worker_name,
        "service_name": runtime_state.service_name,
        "event_type": event_type,
        "job_id": job_id,
        "detail": detail,
        "at": utcnow_iso(),
    }
    await _resolve_redis_call(registry_client.lpush(WORKER_EVENTS_KEY, json.dumps(event_payload)))
    await _resolve_redis_call(registry_client.ltrim(WORKER_EVENTS_KEY, 0, WORKER_EVENT_LIMIT - 1))


if __name__ == "__main__":
    asyncio.run(main())
