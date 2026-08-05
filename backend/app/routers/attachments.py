from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Attachment
from app.schemas.attachments import AttachmentOut
from app.storage import delete_file, file_response, save_upload

router = APIRouter(prefix="/attachments", tags=["attachments"])

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"}
MAX_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def _out(a: Attachment) -> AttachmentOut:
    return AttachmentOut(
        id=a.id, filename=a.filename, contentType=a.content_type, sizeBytes=a.size_bytes,
        uploadedAt=a.uploaded_at.strftime("%d %b %Y %H:%M"),
    )


@router.post("", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    draftToken: str = Form(...), file: UploadFile = File(...), session: AsyncSession = Depends(get_session)
) -> AttachmentOut:
    name = file.filename or "upload"
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}' — allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    storage_path, size = await save_upload(draftToken, file)
    if size > MAX_SIZE_BYTES:
        delete_file(storage_path)
        raise HTTPException(status_code=400, detail="File exceeds the 15 MB limit")

    attachment = Attachment(
        draft_token=draftToken, owner_type=None, owner_id=None, filename=name,
        content_type=file.content_type or "application/octet-stream", size_bytes=size, storage_path=storage_path,
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return _out(attachment)


@router.get("", response_model=list[AttachmentOut])
async def list_draft_attachments(draftToken: str, session: AsyncSession = Depends(get_session)) -> list[AttachmentOut]:
    result = await session.execute(
        select(Attachment).where(Attachment.draft_token == draftToken).order_by(Attachment.uploaded_at)
    )
    return [_out(a) for a in result.scalars().all()]


@router.delete("/{attachment_id}", status_code=204)
async def delete_attachment(attachment_id: int, session: AsyncSession = Depends(get_session)) -> None:
    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    delete_file(attachment.storage_path)
    await session.delete(attachment)
    await session.commit()


@router.get("/{attachment_id}/download")
async def download_attachment(attachment_id: int, session: AsyncSession = Depends(get_session)):
    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return file_response(attachment.storage_path, attachment.filename)
