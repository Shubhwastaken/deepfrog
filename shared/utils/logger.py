import logging
import os
from pathlib import Path

from shared.utils.request_context import get_job_id, get_request_id


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        record.job_id = get_job_id()
        record.service_name = os.getenv("SERVICE_NAME", "app")
        return True


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_customs_brain_configured", False):
        return

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] service=%(service_name)s "
        "request_id=%(request_id)s job_id=%(job_id)s %(name)s: %(message)s"
    )
    context_filter = _ContextFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    root_logger.addHandler(stream_handler)

    log_dir = Path(os.getenv("LOG_DIR", "data/logs")).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    service_name = os.getenv("SERVICE_NAME")
    if service_name:
        file_handler = logging.FileHandler(log_dir / f"{service_name}.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

    root_logger.setLevel(logging.INFO)
    root_logger._customs_brain_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
