from fastapi import APIRouter, UploadFile, File
from app.services.job_service import create_job
from app.services.storage_service import save_file

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = await save_file(file)
    job_id = await create_job(file_path)
    return {"job_id": job_id, "status": "queued"}
