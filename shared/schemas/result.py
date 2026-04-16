from typing import Any, Optional

from pydantic import BaseModel

class ResultSchema(BaseModel):
    job_id: str
    status: str
    document_paths: Optional[dict[str, str]] = None
    results: Optional[dict[str, Any]] = None
    report_path: Optional[str] = None
    error_message: Optional[str] = None
