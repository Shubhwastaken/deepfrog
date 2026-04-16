from fastapi import APIRouter, Depends, HTTPException

from app.db.models import User
from app.services.auth_service import get_current_user
from app.services.job_service import get_job, rerun_job
from shared.schemas.result import ResultSchema

router = APIRouter()


@router.get("/results/{job_id}", response_model=ResultSchema)
async def get_results(job_id: str, current_user: User = Depends(get_current_user)) -> ResultSchema:
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


@router.post("/rerun/{job_id}")
async def rerun_existing_job(job_id: str, current_user: User = Depends(get_current_user)) -> dict:
    """Queue a fresh run using the same source documents as an existing job."""

    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_email and job.owner_email != current_user.email:
        raise HTTPException(status_code=403, detail="You do not have access to this job")

    new_job_id = await rerun_job(job, current_user.email)
    return {
        "job_id": new_job_id,
        "source_job_id": job_id,
        "status": "queued",
    }
