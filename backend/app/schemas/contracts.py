import datetime

from pydantic import BaseModel


class ContractSummary(BaseModel):
    id: str
    vendor: str
    type: str
    contractCategory: str  # 'scope' | 'manpower' — which creation flow this contract came from
    project: str
    valueFmt: str
    progress: str
    progressW: str
    progressColor: str
    expiry: str
    status: str
    typeColor: str
    typeBg: str
    statusColor: str
    statusBg: str


class ContractListResponse(BaseModel):
    items: list[ContractSummary]
    count: int


class LineItemIn(BaseModel):
    code: str
    prLineRef: str
    description: str
    qty: float
    uom: str
    unitRate: float
    budget: float
    slaTags: list[str] = []


class NewContractRequest(BaseModel):
    vendorName: str
    contractorNo: str
    contractType: str  # 'scope' | 'manpower'
    serviceType: str
    projectName: str
    projectNo: str
    durationMonths: int
    contractValue: float
    contractBudget: float
    retentionPct: float = 10
    advancePct: float = 10
    advanceAmount: float
    payableTermsDays: int = 45
    sourcePr: str
    lineItems: list[LineItemIn]
    draftToken: str


class DraftLineItem(BaseModel):
    id: int
    code: str
    prLineRef: str
    description: str
    qty: float
    uom: str
    unitRate: float
    budget: float
    slaTags: list[str] = []


class PaymentTermOptionOut(BaseModel):
    value: float
    label: str


class ContractorOptionOut(BaseModel):
    contractorNo: str
    vendorName: str


class ProjectOptionOut(BaseModel):
    projectNo: str
    projectName: str


class NewContractDraftResponse(BaseModel):
    """Prefill data for the New Contract screen, pulled live from the Oracle PR feed
    (oracle_prs / oracle_pr_lines) rather than hardcoded - the BOQ, payment terms
    percentages, and per-line SLA tags all come from the database and are editable
    in the form before submission.
    """

    sourcePr: str
    vendorName: str
    contractorNo: str
    contractType: str
    serviceType: str
    projectName: str
    projectNo: str
    contractNumberHint: str
    durationMonths: int
    contractValue: float
    contractBudget: float
    retentionPct: float
    advancePct: float
    payableTermsDays: int
    lineItems: list[DraftLineItem]
    prLineCatalog: list[DraftLineItem]
    retentionOptions: list[PaymentTermOptionOut]
    advanceOptions: list[PaymentTermOptionOut]
    payableTermsOptions: list[PaymentTermOptionOut]
    contractorOptions: list[ContractorOptionOut]
    projectOptions: list[ProjectOptionOut]
    serviceTypeOptions: list[str]


class OraclePrOptionOut(BaseModel):
    """One entry in the Oracle PR picker shown before the Scope/Works draft is fetched."""

    id: str
    vendorName: str
    projectName: str
    serviceType: str
    contractValueFmt: str


class ManpowerPositionLineIn(BaseModel):
    categoryPosition: str
    totalStaff: int
    workingHours: float
    basicSalary: float
    hAllowance: float = 0
    tAllowance: float = 0
    fAllowance: float = 0
    share: float = 0
    leaveTreatment: str
    absenceTreatment: str


class NewManpowerContractRequest(BaseModel):
    vendorName: str
    contractorNo: str
    serviceType: str
    issueDate: datetime.date
    expiryTerms: str
    terminationNotice: str
    emailAddress: str
    paymentTermsNote: str
    accountNumber: str
    positionLines: list[ManpowerPositionLineIn]
    draftToken: str


class ManpowerContractDraftResponse(BaseModel):
    """Prefill for the Manpower Supply creation screen — no Oracle PR involved, unlike Scope/Works."""

    contractNumberHint: str
    serviceTypeOptions: list[str]
    contractorOptions: list[ContractorOptionOut]


class ManpowerPositionLineOut(BaseModel):
    categoryPosition: str
    totalStaff: int
    workingHours: str
    basicSalary: str
    hAllowance: str
    tAllowance: str
    fAllowance: str
    share: str
    totalCost: str
    leaveTreatment: str
    absenceTreatment: str


class ManpowerContractSummaryResponse(BaseModel):
    """Read-only summary for a Manpower Supply contract — the rate-card equivalent of the
    Scope/Works IPC tracker, shown instead of it since manpower contracts have no BOQ/IPCs."""

    id: str
    vendorName: str
    contractorNo: str
    serviceType: str
    status: str
    issueDate: str
    expiryTerms: str
    terminationNotice: str
    emailAddress: str
    paymentTermsNote: str
    accountNumber: str
    contractValue: str
    contractBudget: str
    positionLines: list[ManpowerPositionLineOut]


class FinanceCard(BaseModel):
    label: str
    value: str
    note: str
    color: str


class TrackerRow(BaseModel):
    k: str
    v: str
    w: int
    c: str


class TrackerCard(BaseModel):
    title: str
    sub: str
    barW: str
    barColor: str
    rows: list[TrackerRow]


class IpcRow(BaseModel):
    id: int
    n: str
    period: str
    done: str
    gross: str
    ret: str
    adv: str
    net: str
    status: str
    color: str
    bg: str


class TrackingHeader(BaseModel):
    id: str
    vendor: str
    type: str
    project: str
    status: str
    progress: str
    progressColor: str
    remainMonths: str
    expiry: str
    po: str | None
    poRev: str | None
    pr: str | None


class TrackingResponse(BaseModel):
    header: TrackingHeader
    finance: list[FinanceCard]
    trackers: list[TrackerCard]
    ipcs: list[IpcRow]


class IpcCreateRequest(BaseModel):
    period: str
    workDonePct: float
    gross: float


class ApproveContractResponse(BaseModel):
    id: str
    status: str
    oracle_po: str | None
    oracle_po_rev: str | None


class IpcCertificateResponse(BaseModel):
    """Full IPC certificate document for the downloadable/printable page - handed to the contractor."""

    contractId: str
    vendor: str
    contractorNo: str
    project: str
    projectNo: str
    oraclePo: str | None
    oraclePoRev: str | None
    ipcNumber: str
    period: str
    workDonePct: str
    gross: str
    retentionPct: str
    retention: str
    advanceRecovered: str
    netPayable: str
    payableTermsDays: str
    status: str
    createdAt: str


class VendorSubmissionOut(BaseModel):
    """A subcontractor's work-progress claim, simulating the Oracle vendor portal feed."""

    id: int
    period: str
    workDonePct: str
    grossClaimed: str
    submittedBy: str
    submittedAt: str
    status: str  # 'Submitted' | 'Certified'


class SummaryLineItemOut(BaseModel):
    code: str
    prLineRef: str
    description: str
    qty: str
    uom: str
    unitRate: str
    budget: str
    total: str
    slaTags: list[str]
    previousQty: str | None = None
    revisedByCo: str | None = None


class ContractSummaryDocResponse(BaseModel):
    """Full contract document for the downloadable/printable summary page."""

    id: str
    vendor: str
    contractorNo: str
    serviceType: str
    project: str
    projectNo: str
    durationMonths: int
    contractValue: str
    contractBudget: str
    retentionPct: str
    advancePct: str
    payableTermsDays: str
    sourcePr: str | None
    oraclePo: str | None
    oraclePoRev: str | None
    status: str
    createdAt: str
    lineItems: list[SummaryLineItemOut]
