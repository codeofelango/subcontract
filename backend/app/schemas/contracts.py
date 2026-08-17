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
    projectNo: str
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
    oraclePushStatus: str
    oracleConfirmationCode: str | None


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
    poDffRef: str | None
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
    oracle_po_dff_ref: str | None


class ApprovalFlowInfo(BaseModel):
    workflowName: str | None


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


class IpcReportLineOut(BaseModel):
    """One BOQ line's execution breakdown within an IPC report — the gross amount certified for
    this IPC is apportioned across BOQ lines pro-rata to each line's share of the contract BOQ total."""

    code: str
    prLineRef: str
    description: str
    uom: str
    contractQty: str
    unitRate: str
    contractTotal: str
    previousQty: str
    previousAmount: str
    currentQty: str
    currentAmount: str
    totalQty: str
    totalAmount: str


class IpcReportTotals(BaseModel):
    boqGrossTotal: str
    previousAmountTotal: str
    currentAmountTotal: str
    totalExecutedToDate: str
    retentionPct: str
    retentionCurrent: str
    retentionToDate: str
    advancePct: str
    advanceRecoveredCurrent: str
    advanceRecoveredToDate: str
    netPayableCurrent: str
    netPayableToDate: str


class IpcReportAdvanceTracker(BaseModel):
    advancePaid: str
    advanceRecoveredToDate: str
    outstandingAdvance: str


class IpcReportRetentionTracker(BaseModel):
    retentionHeldToDate: str
    retentionReleased: str
    netRetention: str


class IpcReportResponse(BaseModel):
    """BOQ-level progress payment report for one IPC — breaks the certified gross amount down by
    BOQ line item (Previous / Current / Total executed qty & amount), for internal PMO/QS review.
    Complements the simpler IpcCertificateResponse, which is the flat vendor-facing certificate."""

    contractId: str
    vendor: str
    contractorNo: str
    project: str
    projectNo: str
    oraclePo: str | None
    oraclePoRev: str | None
    sourcePr: str | None
    ipcNumber: str
    period: str
    status: str
    createdAt: str
    lines: list[IpcReportLineOut]
    totals: IpcReportTotals
    advanceTracker: IpcReportAdvanceTracker
    retentionTracker: IpcReportRetentionTracker


class IpcInvoiceDeductionRow(BaseModel):
    """One deduction line (Retention / VAT / Advance Tranche / Equipment Rental) with its
    Previous / Current / Total-to-date breakdown, matching the vendor invoice layout."""

    label: str
    rateLabel: str
    previous: str
    current: str
    toDate: str


class IpcInvoiceTotals(BaseModel):
    boqGrossTotal: str
    previousExecuted: str
    currentExecuted: str
    totalExecutedToDate: str
    vatPreviousTotal: str
    vatCurrentTotal: str
    vatToDateTotal: str
    totalExecutedInclVatToDate: str
    deductions: list[IpcInvoiceDeductionRow]
    totalDeductionPrevious: str
    totalDeductionCurrent: str
    totalDeductionToDate: str
    previousNetPaid: str
    netAmountCurrent: str


class IpcInvoiceAdvanceStatement(BaseModel):
    label: str
    pctOfContract: str
    amount: str
    recoveredToDate: str
    outstanding: str
    applicable: bool


class IpcInvoiceRetentionStatement(BaseModel):
    pct: str
    ofAmount: str
    heldToDate: str
    released: str
    netRetention: str


class IpcInvoiceResponse(BaseModel):
    """Full vendor invoice / payment certificate document for one IPC - mirrors the subcontractor's
    own Excel invoice workbook (Invoice + Payment Certificate sheets): BOQ execution breakdown plus
    VAT, dual advance-tranche recovery, equipment rental deduction, and a letter-of-credit tracker."""

    contractId: str
    vendor: str
    project: str
    projectNo: str
    location: str | None
    refNote: str | None
    erpRef: str | None
    contractNumber: str
    invoiceNumber: str
    date: str
    periodFrom: str | None
    periodTo: str | None
    status: str
    lines: list[IpcReportLineOut]
    totals: IpcInvoiceTotals
    advanceStatements: list[IpcInvoiceAdvanceStatement]
    lcStatement: IpcInvoiceAdvanceStatement
    retentionStatement: IpcInvoiceRetentionStatement


class IpcGrnLineOut(BaseModel):
    """One BOQ line's receipt-verified execution, compared against the vendor's self-declared claim
    for the same line. GRN qty/amount comes from actual Goods Receipt Note events; claimed comes from
    apportioning the certified IPC's work-done % across BOQ lines (same basis as the Invoice report)."""

    code: str
    description: str
    uom: str
    contractQty: str
    unitRate: str
    claimedQtyToDate: str
    claimedAmountToDate: str
    grnQtyPrevious: str
    grnAmountPrevious: str
    grnQtyCurrent: str
    grnAmountCurrent: str
    grnQtyToDate: str
    grnAmountToDate: str
    variance: str
    matched: bool


class IpcGrnInvoiceTotals(BaseModel):
    claimedGrossToDate: str
    claimedCompletionPct: str
    grnGrossPrevious: str
    grnGrossCurrent: str
    grnGrossToDate: str
    grnCompletionPct: str
    vatCurrentTotal: str
    vatToDateTotal: str
    deductions: list[IpcInvoiceDeductionRow]
    totalDeductionCurrent: str
    totalDeductionToDate: str
    previousNetPaid: str
    netAmountCurrent: str
    varianceCurrent: str
    varianceFlag: bool


class IpcGrnInvoiceResponse(BaseModel):
    """Invoice / payment certificate whose percentage-completion and billed amounts are grounded in
    Goods Receipt Note (GRN) data - actual received quantities per BOQ line - rather than the vendor's
    self-declared work-done %. Reuses the same VAT / advance-tranche / retention / LC mechanism as
    IpcInvoiceResponse, applied to the GRN-verified gross instead of the certified IPC's gross."""

    contractId: str
    vendor: str
    project: str
    projectNo: str
    location: str | None
    contractNumber: str
    invoiceNumber: str
    date: str
    periodFrom: str | None
    periodTo: str | None
    status: str
    lines: list[IpcGrnLineOut]
    totals: IpcGrnInvoiceTotals
    advanceStatements: list[IpcInvoiceAdvanceStatement]
    lcStatement: IpcInvoiceAdvanceStatement
    retentionStatement: IpcInvoiceRetentionStatement


class VendorSubmissionOut(BaseModel):
    """A subcontractor's work-progress claim, simulating the Oracle vendor portal feed."""

    id: int
    period: str
    workDonePct: str
    grossClaimed: str
    submittedBy: str
    submittedAt: str
    status: str  # 'Submitted' | 'Certified'
    confirmationMessage: str | None = None


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
    oraclePoDffRef: str | None
    status: str
    createdAt: str
    lineItems: list[SummaryLineItemOut]
