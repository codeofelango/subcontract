from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: int
    filename: str
    contentType: str
    sizeBytes: int
    uploadedAt: str
