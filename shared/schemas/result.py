from pydantic import BaseModel
from typing import Optional, List

class ResultSchema(BaseModel):
    job_id: str
    status: str
    hs_codes: Optional[List[dict]] = None
    compliance_issues: Optional[List[dict]] = None
    duty_calculation: Optional[dict] = None
    report_path: Optional[str] = None
