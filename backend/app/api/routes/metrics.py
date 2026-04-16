from fastapi import APIRouter, Depends

from app.db.models import User
from app.services.auth_service import require_admin
from app.services.job_service import get_pipeline_metrics

router = APIRouter()


@router.get("/metrics/pipeline")
async def pipeline_metrics(current_user: User = Depends(require_admin)) -> dict:
    """Return aggregate pipeline job metrics from persistent job storage."""

    return await get_pipeline_metrics()
