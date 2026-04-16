"""Shared helpers for tracking live worker runtime status in Redis."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

WORKER_HEARTBEAT_KEY = "customs_brain:worker_heartbeats"
WORKER_EVENTS_KEY = "customs_brain:worker_events"
WORKER_EVENT_LIMIT = 40
WORKER_HEARTBEAT_STALE_SECONDS = 15


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def decode_redis_value(value: bytes | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def parse_runtime_payload(value: bytes | str | None) -> dict[str, Any] | None:
    decoded_value = decode_redis_value(value)
    if not decoded_value:
        return None
    try:
        payload = json.loads(decoded_value)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def build_worker_status(
    payload: dict[str, Any],
    *,
    stale_after_seconds: int = WORKER_HEARTBEAT_STALE_SECONDS,
) -> dict[str, Any]:
    last_seen_at = payload.get("last_seen_at")
    current_job_id = payload.get("current_job_id")
    is_fresh = False

    if isinstance(last_seen_at, str):
        try:
            seen_at = datetime.fromisoformat(last_seen_at)
            if seen_at.tzinfo is None:
                seen_at = seen_at.replace(tzinfo=UTC)
            is_fresh = datetime.now(UTC) - seen_at <= timedelta(seconds=stale_after_seconds)
        except ValueError:
            is_fresh = False

    status = "offline"
    if is_fresh:
        status = "busy" if current_job_id else "idle"

    return {
        "worker_name": payload.get("worker_name", "unknown-worker"),
        "service_name": payload.get("service_name", "worker"),
        "pid": payload.get("pid"),
        "current_job_id": current_job_id,
        "jobs_completed": int(payload.get("jobs_completed", 0) or 0),
        "jobs_failed": int(payload.get("jobs_failed", 0) or 0),
        "last_seen_at": last_seen_at,
        "status": status,
        "is_fresh": is_fresh,
    }
