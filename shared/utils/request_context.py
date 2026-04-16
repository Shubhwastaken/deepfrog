"""Request and job trace context shared across backend and worker logs."""

from __future__ import annotations

from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_job_id: ContextVar[str] = ContextVar("job_id", default="-")


def set_request_id(request_id: str | None) -> None:
    _request_id.set(request_id or "-")


def get_request_id() -> str:
    return _request_id.get()


def set_job_id(job_id: str | None) -> None:
    _job_id.set(job_id or "-")


def get_job_id() -> str:
    return _job_id.get()


def clear_request_context() -> None:
    set_request_id("-")
    set_job_id("-")
