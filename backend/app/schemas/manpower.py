from pydantic import BaseModel


class ManpowerContext(BaseModel):
    contractId: str
    vendor: str
    period: str
    source: str = "HCM Attendance · post salary-close"
    netVariance: str
    netVarianceColor: str


class ManpowerRow(BaseModel):
    title: str
    reg: str
    regRate: str
    ot: str
    otRate: str
    contract: str
    invoiced: str
    variance: str
    varColor: str
    status: str
    color: str
    bg: str


class ManpowerTotal(BaseModel):
    contract: str
    invoiced: str
    variance: str


class ManpowerResponse(BaseModel):
    context: ManpowerContext
    rows: list[ManpowerRow]
    total: ManpowerTotal
    varianceNote: str | None = None
    matchedTotal: str
