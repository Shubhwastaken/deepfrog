from fastapi import APIRouter
router = APIRouter()

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    return {"job_id": job_id, "status": "processing", "results": None}
