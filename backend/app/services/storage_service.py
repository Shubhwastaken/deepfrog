import os, aiofiles
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_file(file: UploadFile) -> str:
    path = os.path.join(UPLOAD_DIR, file.filename)
    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())
    return path
