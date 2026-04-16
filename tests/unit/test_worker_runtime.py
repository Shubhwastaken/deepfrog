from shared.utils.worker_runtime import build_worker_status


def test_build_worker_status_marks_busy_worker_as_fresh():
    worker = build_worker_status(
        {
            "worker_name": "worker-a",
            "service_name": "worker-a",
            "pid": 1234,
            "current_job_id": "job-1",
            "jobs_completed": 2,
            "jobs_failed": 1,
            "last_seen_at": "2099-01-01T00:00:00+00:00",
        }
    )

    assert worker["worker_name"] == "worker-a"
    assert worker["status"] == "busy"
    assert worker["is_fresh"] is True


def test_build_worker_status_marks_stale_worker_offline():
    worker = build_worker_status(
        {
            "worker_name": "worker-b",
            "service_name": "worker-b",
            "pid": 5678,
            "current_job_id": None,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "last_seen_at": "2000-01-01T00:00:00+00:00",
        }
    )

    assert worker["status"] == "offline"
    assert worker["is_fresh"] is False
