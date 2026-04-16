from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.db.models import User
from app.services.job_service import get_job
from app.services.local_jobs import get_local_job
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/results/{job_id}/report")
async def download_report(job_id: str, current_user: User = Depends(get_current_user)) -> FileResponse:
    """Download the generated markdown report for a completed job."""

    if settings.LOCAL_PIPELINE_MODE:
        job = get_local_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["owner_email"] != current_user.email:
            raise HTTPException(status_code=403, detail="You do not have access to this report")
        report_path_value = job["report_path"]
    else:
        job = await get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.owner_email and job.owner_email != current_user.email:
            raise HTTPException(status_code=403, detail="You do not have access to this report")
        report_path_value = job.report_path

    if not report_path_value:
        raise HTTPException(status_code=404, detail="Report not available yet")

    report_path = Path(report_path_value)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file is missing")

    return FileResponse(
        path=report_path,
        filename=report_path.name,
        media_type="text/markdown",
    )
