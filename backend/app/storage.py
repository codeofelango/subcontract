"""File storage abstraction for uploaded attachments, backed by Azure Blob Storage.

storage_path is the blob name within settings.azure_storage_container, shaped
<key>/<uuid>_<filename> (key is the draft_token, matching the pre-Azure disk layout).
"""

import uuid
from pathlib import Path

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient as SyncBlobServiceClient
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Attachment


def _sync_container_client():
    return SyncBlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    ).get_container_client(settings.azure_storage_container)


async def save_upload(key: str, file: UploadFile) -> tuple[str, int]:
    """Uploads to <key>/<uuid>_<filename> in the attachments container. Returns (storage_path, size_bytes)."""
    safe_name = Path(file.filename or "upload").name
    blob_name = f"{key}/{uuid.uuid4().hex}_{safe_name}"
    content = await file.read()

    async with AsyncBlobServiceClient.from_connection_string(settings.azure_storage_connection_string) as client:
        await client.get_container_client(settings.azure_storage_container).upload_blob(
            name=blob_name, data=content, overwrite=True
        )

    return blob_name, len(content)


def file_response(storage_path: str, filename: str) -> StreamingResponse:
    downloader = _sync_container_client().download_blob(storage_path)
    return StreamingResponse(
        downloader.chunks(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def delete_file(storage_path: str) -> None:
    try:
        _sync_container_client().delete_blob(storage_path)
    except ResourceNotFoundError:
        pass


def read_bytes(storage_path: str) -> bytes:
    return _sync_container_client().download_blob(storage_path).readall()


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
