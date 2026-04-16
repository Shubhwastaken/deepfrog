from typing import Any, Optional

from pydantic import BaseModel

class ResultSchema(BaseModel):
    job_id: str
    status: str
    results: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
