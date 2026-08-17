"""File storage abstraction for uploaded attachments.

Backed by local disk for now (backend/uploads/, gitignored) - swapping to Azure Blob Storage
later means rewriting only this module (save_upload/file_response/delete_file) using
azure-storage-blob's BlobServiceClient; nothing in routers/schemas/the frontend would change.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Attachment

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"


async def save_upload(key: str, file: UploadFile) -> tuple[str, int]:
    """Writes the upload under uploads/<key>/<uuid>_<filename>. Returns (storage_path, size_bytes)."""
    directory = UPLOAD_ROOT / key
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload").name
    disk_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = directory / disk_name

    size = 0
    with destination.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            out.write(chunk)

    return str(destination.relative_to(UPLOAD_ROOT.parent)), size


def file_response(storage_path: str, filename: str) -> FileResponse:
    full_path = UPLOAD_ROOT.parent / storage_path
    return FileResponse(full_path, filename=filename)


def delete_file(storage_path: str) -> None:
    full_path = UPLOAD_ROOT.parent / storage_path
    full_path.unlink(missing_ok=True)


def read_bytes(storage_path: str) -> bytes:
    return (UPLOAD_ROOT.parent / storage_path).read_bytes()


async def claim_attachments(session: AsyncSession, draft_token: str, owner_type: str, owner_id: str) -> None:
    """Re-parents every attachment uploaded under a draft_token to the now-created real record."""
    await session.execute(
        update(Attachment)
        .where(Attachment.draft_token == draft_token)
        .values(owner_type=owner_type, owner_id=owner_id, draft_token=None)
    )


async def require_attachment(session: AsyncSession, draft_token: str) -> None:
    """Raised by any create-flow whose owner type mandates at least one supporting document."""
    exists = await session.scalar(select(Attachment.id).where(Attachment.draft_token == draft_token).limit(1))
    if not exists:
        raise HTTPException(status_code=400, detail="At least one supporting document is required")


async def get_owner_attachments(session: AsyncSession, owner_type: str, owner_id: str) -> list[Attachment]:
    result = await session.execute(
        select(Attachment).where(Attachment.owner_type == owner_type, Attachment.owner_id == owner_id).order_by(Attachment.uploaded_at)
    )
    return list(result.scalars().all())
