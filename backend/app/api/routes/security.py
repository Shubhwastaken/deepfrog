from fastapi import APIRouter, Depends

from app.db.models import User
from app.services.auth_service import require_admin
from app.services.security_service import get_security_storage_proof

router = APIRouter()


@router.get("/security/storage")
async def security_storage(current_user: User = Depends(require_admin)) -> dict:
    """Return admin-facing database encryption proof for demos and audits."""

    return await get_security_storage_proof()
