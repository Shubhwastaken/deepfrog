from fastapi import APIRouter, Depends, File, UploadFile

from app.db.models import User
from app.services.auth_service import get_current_user
from app.services.job_service import create_job
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

    job_id = await create_job(invoice_path, bill_of_lading_path, current_user.email)
    return {
        "job_id": job_id,
        "status": "queued",
    }
