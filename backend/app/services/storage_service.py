import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_file(file: UploadFile, *, prefix: str) -> str:
    """Persist an uploaded file under a unique name in shared storage."""

    import aiofiles

    safe_name = Path(file.filename or f"{prefix}.bin").name
    target_name = f"{prefix}-{uuid4().hex}-{safe_name}"
    path = (UPLOAD_DIR / target_name).resolve()
    async with aiofiles.open(path, "wb") as file_obj:
        await file_obj.write(await file.read())
    return str(path)
