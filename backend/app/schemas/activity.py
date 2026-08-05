from pydantic import BaseModel


class ActivityEntryOut(BaseModel):
    id: int
    contractId: str | None
    entityType: str
    entityId: str
    action: str
    summary: str
    actor: str
    createdAt: str


class AskActivityRequest(BaseModel):
    question: str


class AskActivityResponse(BaseModel):
    answer: str
    matches: list[ActivityEntryOut]
