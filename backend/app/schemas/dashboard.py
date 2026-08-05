from pydantic import BaseModel


class KpiItem(BaseModel):
    label: str
    value: str
    delta: str
    deltaColor: str


class AlertItem(BaseModel):
    title: str
    detail: str
    tag: str
    color: str
    bg: str


class ServiceMixItem(BaseModel):
    label: str
    amount: str
    pct: str
    width: str
    color: str


class PendingActionItem(BaseModel):
    ref: str
    item: str
    vendor: str
    stage: str
    amount: str
    age: str
    color: str
    bg: str


class VendorSummaryItem(BaseModel):
    vendor: str
    contractorNo: str
    contractsCount: int
    activeCount: int
    totalValue: str
    avgProgress: str
    progressColor: str
    rating: str
    ratingColor: str
    ratingBg: str


class DashboardResponse(BaseModel):
    kpis: list[KpiItem]
    alerts: list[AlertItem]
    serviceMix: list[ServiceMixItem]
    pendingActions: list[PendingActionItem]
    vendors: list[VendorSummaryItem]
