from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.db.models import User
from app.services.job_service import get_job
from app.services.local_jobs import get_local_job
from app.services.auth_service import get_current_user
from shared.schemas.result import ResultSchema

router = APIRouter()

@router.get("/results/{job_id}", response_model=ResultSchema)
async def get_results(job_id: str, current_user: User = Depends(get_current_user)) -> ResultSchema:
    if settings.LOCAL_PIPELINE_MODE:
        job = get_local_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job["owner_email"] != current_user.email:
            raise HTTPException(status_code=403, detail="You do not have access to this job")
        return ResultSchema(
            job_id=job["job_id"],
            status=job["status"],
            results=job["results"],
            error_message=job["error_message"],
        )

    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_email and job.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="You do not have access to this job")

    return ResultSchema(
        job_id=job.id,
        status=job.status,
        results=job.results,
        error_message=job.error_message,
    )
