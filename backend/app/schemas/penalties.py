from pydantic import BaseModel

from app.schemas.attachments import AttachmentOut
from app.schemas.change_orders import ApprovalStepOut


class PenaltyField(BaseModel):
    label: str
    value: str
    weight: int
    color: str


class SlaBreach(BaseModel):
    actualPct: str
    label: str
    detail: str


class PenaltyDetailResponse(BaseModel):
    id: str
    title: str
    status: str
    fields: list[PenaltyField]
    attachment: str
    attachments: list[AttachmentOut]
    slaBreach: SlaBreach
    approvalSteps: list[ApprovalStepOut]


class NewPenaltyRequest(BaseModel):
    contractId: str
    reason: str
    basis: str
    amount: float
    draftToken: str
    raisedBy: str
    slaActualPct: float
    slaTargetPct: float
    slaBreachMonths: int
    slaLabel: str = "SLA Score"
