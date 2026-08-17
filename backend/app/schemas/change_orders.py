import datetime

from pydantic import BaseModel


class CoContext(BaseModel):
    id: str
    title: str
    contractId: str
    vendor: str
    po: str
    status: str


class CoLineRow(BaseModel):
    code: str
    desc: str
    orig: str
    rev: str
    delta: str
    deltaColor: str
    rate: str
    impact: str
    impactColor: str


class CoHistoryRow(BaseModel):
    id: str
    reason: str
    impact: str
    impactColor: str
    po: str
    status: str
    color: str
    bg: str


class CoValueRow(BaseModel):
    k: str
    v: str
    w: int
    c: str


class ApprovalStepOut(BaseModel):
    id: int | None = None
    seq: int
    role: str
    name: str
    meta: str
    state: str  # done | current | pending | rejected | skipped
    decision: str | None = None  # approved | rejected
    actedBy: str | None = None
    actedAt: datetime.datetime | None = None


class DecisionRequest(BaseModel):
    decision: str  # "approved" | "rejected"
    comment: str | None = None


class ReviseDecisionRequest(BaseModel):
    decision: str  # "approved" | "rejected"
    reason: str


class ChangeOrderDetailResponse(BaseModel):
    context: CoContext
    affectedLineItems: list[CoLineRow]
    history: list[CoHistoryRow]
    valueRows: list[CoValueRow]
    approvalSteps: list[ApprovalStepOut]


class NewCoLine(BaseModel):
    code: str
    description: str
    originalQty: float
    revisedQty: float
    contractRate: float


class NewChangeOrderRequest(BaseModel):
    contractId: str
    title: str
    reason: str
    lines: list[NewCoLine]
