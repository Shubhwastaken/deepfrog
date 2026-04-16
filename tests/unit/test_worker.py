import asyncio
from unittest.mock import AsyncMock

import pytest

from workers import worker


def test_process_job_payload_marks_job_completed(monkeypatch):
    update_job_processing = AsyncMock()
    route_task = AsyncMock(return_value={"output_result": {"status": "ok"}})
    update_job_completed = AsyncMock()
    update_job_failed = AsyncMock()

    monkeypatch.setattr(worker, "update_job_processing", update_job_processing)
    monkeypatch.setattr(worker, "route_task", route_task)
    monkeypatch.setattr(worker, "update_job_completed", update_job_completed)
    monkeypatch.setattr(worker, "update_job_failed", update_job_failed)

    asyncio.run(
        worker.process_job_payload(
            {
                "job_id": "job-123",
                "document_paths": {"invoice": "invoice.pdf", "bill_of_lading": "bol.pdf"},
            }
        )
    )

    update_job_processing.assert_awaited_once_with("job-123")
    route_task.assert_awaited_once_with(
        "job-123", {"invoice": "invoice.pdf", "bill_of_lading": "bol.pdf"}
    )
    update_job_completed.assert_awaited_once_with("job-123", {"output_result": {"status": "ok"}})
    update_job_failed.assert_not_awaited()


def test_process_job_payload_marks_invalid_document_paths_failed(monkeypatch):
    update_job_processing = AsyncMock()
    route_task = AsyncMock()
    update_job_completed = AsyncMock()
    update_job_failed = AsyncMock()

    monkeypatch.setattr(worker, "update_job_processing", update_job_processing)
    monkeypatch.setattr(worker, "route_task", route_task)
    monkeypatch.setattr(worker, "update_job_completed", update_job_completed)
    monkeypatch.setattr(worker, "update_job_failed", update_job_failed)

    asyncio.run(worker.process_job_payload({"job_id": "job-123", "document_paths": ["bad-shape"]}))

    update_job_processing.assert_not_awaited()
    route_task.assert_not_awaited()
    update_job_completed.assert_not_awaited()
    update_job_failed.assert_awaited_once_with(
        "job-123", "Queue payload missing valid document_paths."
    )


def test_process_job_payload_requires_job_id():
    with pytest.raises(ValueError, match="job_id"):
        asyncio.run(worker.process_job_payload({"document_paths": {"invoice": "invoice.pdf"}}))
