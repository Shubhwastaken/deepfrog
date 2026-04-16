import os
import uuid
import aiofiles
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_file(file: UploadFile) -> str:
    """Save a single uploaded file (legacy endpoint)."""
    path = os.path.join(UPLOAD_DIR, file.filename)
    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())
    return path


async def save_upload_pair(invoice: UploadFile, bol: UploadFile) -> tuple[str, str]:
    """
    Save invoice + BOL file pair with UUID-prefixed names to avoid collisions.
    Returns (invoice_path, bol_path).
    """
    prefix = uuid.uuid4().hex[:8]

    invoice_name = f"invoice_{prefix}_{invoice.filename}"
    bol_name = f"bol_{prefix}_{bol.filename}"

    invoice_path = os.path.join(UPLOAD_DIR, invoice_name)
    bol_path = os.path.join(UPLOAD_DIR, bol_name)

    async with aiofiles.open(invoice_path, "wb") as f:
        await f.write(await invoice.read())

    async with aiofiles.open(bol_path, "wb") as f:
        await f.write(await bol.read())

    return os.path.abspath(invoice_path), os.path.abspath(bol_path)
