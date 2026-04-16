import asyncio

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.db.models import User
from app.services.job_service import create_job
from app.services.local_jobs import create_local_job, process_local_job
from app.services.auth_service import get_current_user
from app.services.storage_service import save_file

router = APIRouter()

@router.post("/upload")
async def upload_document(
    invoice: UploadFile = File(...),
    bill_of_lading: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload the two required shipping documents and queue a job."""

    invoice_path = await save_file(invoice, prefix="invoice")
    bill_of_lading_path = await save_file(bill_of_lading, prefix="bill-of-lading")

    if settings.LOCAL_PIPELINE_MODE:
        job = create_local_job(invoice_path, bill_of_lading_path, current_user.email)
        asyncio.create_task(process_local_job(job["job_id"]))
        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "document_paths": job["document_paths"],
        }

    job_id = await create_job(invoice_path, bill_of_lading_path, current_user.email)
    return {
        "job_id": job_id,
        "status": "queued",
        "document_paths": {
            "invoice": invoice_path,
            "bill_of_lading": bill_of_lading_path,
        },
    }
