import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.business import fmt_num, join_tags, money, progress_color, split_tags, status_colors, type_colors
from app.database import get_session
from app.models import (
    Attachment,
    ApprovalStep,
    Contract,
    ContractLineItem,
    Ipc,
    ManpowerContractDetail,
    ManpowerPositionLine,
    OracleContractor,
    OraclePr,
    OraclePrLine,
    OracleProject,
    PaymentTermOption,
    ServiceTypeOption,
    VendorPortalSubmission,
)
from app.schemas.attachments import AttachmentOut
from app.schemas.change_orders import ApprovalStepOut
from app.storage import claim_attachments
from app.workflow_engine import resolve_chain, seed_approval_steps
from app.schemas.contracts import (
    ApproveContractResponse,
    ContractListResponse,
    ContractorOptionOut,
    ContractSummary,
    ContractSummaryDocResponse,
    DraftLineItem,
    FinanceCard,
    IpcCertificateResponse,
    IpcCreateRequest,
    IpcRow,
    ManpowerContractDraftResponse,
    ManpowerContractSummaryResponse,
    ManpowerPositionLineOut,
    NewContractDraftResponse,
    NewContractRequest,
    NewManpowerContractRequest,
    OraclePrOptionOut,
    PaymentTermOptionOut,
    ProjectOptionOut,
    SummaryLineItemOut,
    TrackerCard,
    TrackerRow,
    TrackingHeader,
    TrackingResponse,
    VendorSubmissionOut,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _summary(c: Contract) -> ContractSummary:
    tc, tbg = type_colors(c.service_type)
    sc, sbg = status_colors(c.status)
    return ContractSummary(
        id=c.id,
        vendor=c.vendor_name,
        type=c.service_type,
        contractCategory=c.contract_type,
        project=c.project_name or "—",
        valueFmt=money(c.contract_value),
        progress=f"{c.progress_pct}%",
        progressW=f"{c.progress_pct}%",
        progressColor=progress_color(c.progress_pct),
        expiry=c.expiry_date.strftime("%d %b %Y") if c.expiry_date else "—",
        status=c.status,
        typeColor=tc,
        typeBg=tbg,
        statusColor=sc,
        statusBg=sbg,
    )


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    project: str | None = None,
    serviceType: str | None = None,
    vendor: str | None = None,
    status: str | None = None,
    expiryWithinDays: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> ContractListResponse:
    stmt = select(Contract)
    if project and project != "All":
        stmt = stmt.where(Contract.project_name == project)
    if serviceType and serviceType != "All":
        stmt = stmt.where(Contract.service_type == serviceType)
    if vendor and vendor != "All":
        stmt = stmt.where(Contract.vendor_name == vendor)
    if status and status != "All":
        stmt = stmt.where(Contract.status == status)
    if expiryWithinDays is not None:
        cutoff = datetime.date.today() + datetime.timedelta(days=expiryWithinDays)
        stmt = stmt.where(Contract.expiry_date <= cutoff)
    stmt = stmt.order_by(Contract.id)

    result = await session.execute(stmt)
    contracts = result.scalars().all()
    items = [_summary(c) for c in contracts]
    return ContractListResponse(items=items, count=len(items))


async def _next_contract_number(session: AsyncSession) -> str:
    result = await session.execute(select(Contract).order_by(Contract.id.desc()).limit(1))
    last = result.scalars().first()
    year = datetime.date.today().year
    seq = 1
    if last and last.id.startswith(f"SC-{year}"):
        seq = int(last.id.split("-")[-1]) + 1
    return f"SC-{year}-{seq:04d}"


async def _service_type_options(session: AsyncSession, category: str) -> list[str]:
    result = await session.execute(
        select(ServiceTypeOption)
        .where(ServiceTypeOption.contract_category.in_([category, "both"]))
        .order_by(ServiceTypeOption.sort_order)
    )
    return [o.label for o in result.scalars().all()]


@router.get("/oracle-prs", response_model=list[OraclePrOptionOut])
async def list_oracle_prs(session: AsyncSession = Depends(get_session)) -> list[OraclePrOptionOut]:
    """Approved Oracle PRs available to draft a Scope/Works contract from - the picker shown
    before the BOQ draft screen, instead of always auto-selecting the first PR in the feed.
    """
    result = await session.execute(select(OraclePr).order_by(OraclePr.id))
    return [
        OraclePrOptionOut(
            id=pr.id, vendorName=pr.vendor_name, projectName=pr.project_name,
            serviceType=pr.service_type, contractValueFmt=money(pr.contract_value),
        )
        for pr in result.scalars().all()
    ]


@router.get("/new/draft", response_model=NewContractDraftResponse)
async def new_contract_draft(pr: str | None = None, session: AsyncSession = Depends(get_session)) -> NewContractDraftResponse:
    """Prefill for the New Contract screen, pulled live from the Oracle PR feed (oracle_prs / oracle_pr_lines)
    rather than hardcoded - simulates PR lines flowing in from Oracle until real integration is wired up.
    """
    stmt = select(OraclePr).order_by(OraclePr.id)
    if pr:
        stmt = stmt.where(OraclePr.id == pr)
    result = await session.execute(stmt)
    pr_header = result.scalars().first()
    if not pr_header:
        raise HTTPException(status_code=404, detail="No approved Oracle PR available to draft a contract from")

    lines_result = await session.execute(select(OraclePrLine).where(OraclePrLine.pr_id == pr_header.id).order_by(OraclePrLine.id))
    lines = lines_result.scalars().all()

    catalog_result = await session.execute(select(OraclePrLine).order_by(OraclePrLine.pr_id, OraclePrLine.id))
    catalog_lines = catalog_result.scalars().all()

    def _to_draft_line_item(li: OraclePrLine) -> DraftLineItem:
        return DraftLineItem(
            id=li.id, code=li.code, prLineRef=li.pr_line_ref, description=li.description,
            qty=float(li.qty), uom=li.uom, unitRate=float(li.unit_rate), budget=float(li.budget),
            slaTags=split_tags(li.sla_tags),
        )

    async def _options(category: str) -> list[PaymentTermOptionOut]:
        result = await session.execute(
            select(PaymentTermOption).where(PaymentTermOption.category == category).order_by(PaymentTermOption.sort_order)
        )
        return [PaymentTermOptionOut(value=float(o.value), label=o.label) for o in result.scalars().all()]

    return NewContractDraftResponse(
        sourcePr=pr_header.id,
        vendorName=pr_header.vendor_name,
        contractorNo=pr_header.contractor_no,
        contractType=pr_header.contract_type,
        serviceType=pr_header.service_type,
        projectName=pr_header.project_name,
        projectNo=pr_header.project_no,
        contractNumberHint=await _next_contract_number(session),
        durationMonths=pr_header.duration_months,
        contractValue=float(pr_header.contract_value),
        contractBudget=float(pr_header.contract_budget),
        retentionPct=float(pr_header.retention_pct),
        advancePct=float(pr_header.advance_pct),
        payableTermsDays=pr_header.payable_terms_days,
        lineItems=[_to_draft_line_item(li) for li in lines],
        prLineCatalog=[_to_draft_line_item(li) for li in catalog_lines],
        retentionOptions=await _options("retention_pct"),
        advanceOptions=await _options("advance_pct"),
        payableTermsOptions=await _options("payable_terms_days"),
        contractorOptions=[
            ContractorOptionOut(contractorNo=c.contractor_no, vendorName=c.vendor_name)
            for c in (await session.execute(select(OracleContractor).order_by(OracleContractor.vendor_name))).scalars().all()
        ],
        projectOptions=[
            ProjectOptionOut(projectNo=p.project_no, projectName=p.project_name)
            for p in (await session.execute(select(OracleProject).order_by(OracleProject.project_name))).scalars().all()
        ],
        serviceTypeOptions=await _service_type_options(session, "scope"),
    )


@router.get("/new/manpower-draft", response_model=ManpowerContractDraftResponse)
async def new_manpower_contract_draft(session: AsyncSession = Depends(get_session)) -> ManpowerContractDraftResponse:
    """Prefill for the Manpower Supply creation screen. Unlike Scope/Works, this flow has no Oracle
    PR trigger - it starts from a blank contractor + rate-card form, per CLAUDE.md's domain rules.
    """
    return ManpowerContractDraftResponse(
        contractNumberHint=await _next_contract_number(session),
        serviceTypeOptions=await _service_type_options(session, "manpower"),
        contractorOptions=[
            ContractorOptionOut(contractorNo=c.contractor_no, vendorName=c.vendor_name)
            for c in (await session.execute(select(OracleContractor).order_by(OracleContractor.vendor_name))).scalars().all()
        ],
    )


CONTRACT_APPLIES_TO_VALUES = {"contract_scope", "contract_manpower"}


@router.get("/new/approval-preview", response_model=list[ApprovalStepOut])
async def preview_approval_chain(appliesTo: str, session: AsyncSession = Depends(get_session)) -> list[ApprovalStepOut]:
    """What the approval chain WILL be if this contract is submitted right now - shown on the
    New Contract screen before submission so the raiser knows the full routing and every named
    approver up front. Empty list means no flow is configured/activated for this type yet (the
    contract will use the plain one-shot /approve instead of a chain).
    """
    if appliesTo not in CONTRACT_APPLIES_TO_VALUES:
        raise HTTPException(status_code=400, detail=f"appliesTo must be one of {sorted(CONTRACT_APPLIES_TO_VALUES)}")

    rows = await resolve_chain(session, appliesTo, fallback_template=[])
    steps: list[ApprovalStepOut] = []
    for i, r in enumerate(rows):
        user = r["user"]
        name = f"{user.name} — {user.title}" if user else "Raised by you"
        state = "done" if i == 0 else ("current" if i == 1 else "pending")
        meta = (
            "Marked complete on submit" if state == "done"
            else ("Will require approval immediately after submit" if state == "current" else "Pending")
        )
        steps.append(ApprovalStepOut(seq=i, role=r["role"], name=name, meta=meta, state=state))
    return steps


async def _require_attachment(session: AsyncSession, draft_token: str) -> None:
    exists = await session.scalar(select(Attachment.id).where(Attachment.draft_token == draft_token).limit(1))
    if not exists:
        raise HTTPException(status_code=400, detail="At least one supporting document is required")


@router.post("", response_model=ContractSummary, status_code=201)
async def create_contract(payload: NewContractRequest, session: AsyncSession = Depends(get_session)) -> ContractSummary:
    await _require_attachment(session, payload.draftToken)
    new_id = await _next_contract_number(session)

    contract = Contract(
        id=new_id,
        vendor_name=payload.vendorName,
        contractor_no=payload.contractorNo,
        contract_type=payload.contractType,
        service_type=payload.serviceType,
        project_name=payload.projectName,
        project_no=payload.projectNo,
        duration_months=payload.durationMonths,
        contract_value=Decimal(str(payload.contractValue)),
        contract_budget=Decimal(str(payload.contractBudget)),
        retention_pct=Decimal(str(payload.retentionPct)),
        advance_pct=Decimal(str(payload.advancePct)),
        advance_amount=Decimal(str(payload.advanceAmount)),
        payable_terms_days=payload.payableTermsDays,
        source_pr=payload.sourcePr,
        oracle_po=None,
        oracle_po_rev=None,
        status="Pending",
        progress_pct=0,
        remaining_months=payload.durationMonths,
    )
    session.add(contract)
    for li in payload.lineItems:
        session.add(ContractLineItem(
            contract_id=new_id, code=li.code, pr_line_ref=li.prLineRef, description=li.description,
            qty=Decimal(str(li.qty)), uom=li.uom, unit_rate=Decimal(str(li.unitRate)),
            budget=Decimal(str(li.budget)), total=Decimal(str(li.qty)) * Decimal(str(li.unitRate)),
            sla_tags=join_tags(li.slaTags),
        ))
    await seed_approval_steps(session, owner_type="contract", owner_id=new_id, applies_to="contract_scope", fallback_template=[], raiser_name="")
    await claim_attachments(session, payload.draftToken, "contract", new_id)

    log_activity(
        session, entity_type="contract", entity_id=new_id, action="created", contract_id=new_id,
        summary=f"Contract {new_id} created for {payload.vendorName} — {payload.projectName} ({payload.serviceType}), value {money(Decimal(str(payload.contractValue)))}",
    )
    await session.commit()
    await session.refresh(contract)
    return _summary(contract)


def _position_line_total_cost(li) -> Decimal:
    return (
        Decimal(str(li.basicSalary)) + Decimal(str(li.hAllowance)) + Decimal(str(li.tAllowance))
        + Decimal(str(li.fAllowance)) + Decimal(str(li.share))
    )


@router.post("/manpower", response_model=ContractSummary, status_code=201)
async def create_manpower_contract(
    payload: NewManpowerContractRequest, session: AsyncSession = Depends(get_session)
) -> ContractSummary:
    """Manpower Supply contracts are created without an Oracle PR - no BOQ, no retention/advance,
    a rate-card (position lines) instead. Kept as a separate endpoint from Scope/Works so the two
    flows never share validation rules, per CLAUDE.md's domain rules.
    """
    if not payload.positionLines:
        raise HTTPException(status_code=400, detail="At least one position line is required")
    await _require_attachment(session, payload.draftToken)

    new_id = await _next_contract_number(session)
    position_totals = [(li, _position_line_total_cost(li)) for li in payload.positionLines]
    contract_value = sum((total * li.totalStaff for li, total in position_totals), Decimal("0"))

    contract = Contract(
        id=new_id,
        vendor_name=payload.vendorName,
        contractor_no=payload.contractorNo,
        contract_type="manpower",
        service_type=payload.serviceType,
        project_name=None,
        project_no=None,
        duration_months=0,
        contract_value=contract_value,
        contract_budget=contract_value,
        retention_pct=Decimal("0"),
        advance_pct=Decimal("0"),
        advance_amount=Decimal("0"),
        payable_terms_days=0,
        source_pr=None,
        oracle_po=None,
        oracle_po_rev=None,
        status="Pending",
        progress_pct=0,
        remaining_months=0,
    )
    session.add(contract)
    session.add(ManpowerContractDetail(
        contract_id=new_id, issue_date=payload.issueDate, expiry_terms=payload.expiryTerms,
        termination_notice=payload.terminationNotice, email_address=payload.emailAddress,
        payment_terms_note=payload.paymentTermsNote, account_number=payload.accountNumber,
    ))
    for li, total_cost in position_totals:
        session.add(ManpowerPositionLine(
            contract_id=new_id, category_position=li.categoryPosition, total_staff=li.totalStaff,
            working_hours=Decimal(str(li.workingHours)), basic_salary=Decimal(str(li.basicSalary)),
            h_allowance=Decimal(str(li.hAllowance)), t_allowance=Decimal(str(li.tAllowance)),
            f_allowance=Decimal(str(li.fAllowance)), share=Decimal(str(li.share)), total_cost=total_cost,
            leave_treatment=li.leaveTreatment, absence_treatment=li.absenceTreatment,
        ))
    await seed_approval_steps(session, owner_type="contract", owner_id=new_id, applies_to="contract_manpower", fallback_template=[], raiser_name="")
    await claim_attachments(session, payload.draftToken, "contract", new_id)

    log_activity(
        session, entity_type="contract", entity_id=new_id, action="created", contract_id=new_id,
        summary=f"Manpower Supply contract {new_id} created for {payload.vendorName}, value {money(contract_value)}",
    )
    await session.commit()
    await session.refresh(contract)
    return _summary(contract)


@router.get("/{contract_id}/manpower-summary", response_model=ManpowerContractSummaryResponse)
async def manpower_contract_summary(contract_id: str, session: AsyncSession = Depends(get_session)) -> ManpowerContractSummaryResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.contract_type != "manpower":
        raise HTTPException(status_code=400, detail="Not a Manpower Supply contract")

    detail = await session.get(ManpowerContractDetail, contract_id)
    result = await session.execute(
        select(ManpowerPositionLine).where(ManpowerPositionLine.contract_id == contract_id).order_by(ManpowerPositionLine.id)
    )
    lines = result.scalars().all()

    return ManpowerContractSummaryResponse(
        id=contract.id,
        vendorName=contract.vendor_name,
        contractorNo=contract.contractor_no,
        serviceType=contract.service_type,
        status=contract.status,
        issueDate=detail.issue_date.strftime("%d %b %Y") if detail else "—",
        expiryTerms=detail.expiry_terms if detail else "—",
        terminationNotice=detail.termination_notice if detail else "—",
        emailAddress=detail.email_address if detail else "—",
        paymentTermsNote=detail.payment_terms_note if detail else "—",
        accountNumber=detail.account_number if detail else "—",
        contractValue=money(contract.contract_value),
        contractBudget=money(contract.contract_budget),
        positionLines=[
            ManpowerPositionLineOut(
                categoryPosition=li.category_position, totalStaff=li.total_staff, workingHours=fmt_num(li.working_hours),
                basicSalary=money(li.basic_salary), hAllowance=money(li.h_allowance), tAllowance=money(li.t_allowance),
                fAllowance=money(li.f_allowance), share=money(li.share), totalCost=money(li.total_cost),
                leaveTreatment=li.leave_treatment, absenceTreatment=li.absence_treatment,
            )
            for li in lines
        ],
    )


async def _contract_approval_steps(session: AsyncSession, contract_id: str) -> list[ApprovalStep]:
    result = await session.execute(
        select(ApprovalStep).where(ApprovalStep.owner_type == "contract", ApprovalStep.owner_id == contract_id).order_by(ApprovalStep.seq)
    )
    return list(result.scalars().all())


def _activate_contract(contract: Contract) -> str:
    contract.status = "Active"
    if contract.contract_type == "scope":
        contract.oracle_po = f"PO-ORA-{440000 + int(contract.id.split('-')[-1]):d}"
        contract.oracle_po_rev = "Rev 1"
        return f"Contract {contract.id} approved — Oracle PO {contract.oracle_po} ({contract.oracle_po_rev}) created for {contract.vendor_name}"
    return f"Manpower Supply contract {contract.id} approved for {contract.vendor_name}"


@router.get("/{contract_id}/approval-steps", response_model=list[ApprovalStepOut])
async def get_contract_approval_steps(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[ApprovalStepOut]:
    """Empty unless an admin has built and activated a Contract approval flow in /approval-flows —
    otherwise contracts use the plain one-shot /approve below, same as before that feature existed.
    """
    steps = await _contract_approval_steps(session, contract_id)
    return [ApprovalStepOut(seq=s.seq, role=s.role, name=s.approver_name, meta=s.meta_note, state=s.state) for s in steps]


@router.get("/{contract_id}/attachments", response_model=list[AttachmentOut])
async def get_contract_attachments(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[AttachmentOut]:
    result = await session.execute(
        select(Attachment).where(Attachment.owner_type == "contract", Attachment.owner_id == contract_id).order_by(Attachment.uploaded_at)
    )
    return [
        AttachmentOut(id=a.id, filename=a.filename, contentType=a.content_type, sizeBytes=a.size_bytes, uploadedAt=a.uploaded_at.strftime("%d %b %Y %H:%M"))
        for a in result.scalars().all()
    ]


@router.post("/{contract_id}/approve", response_model=ApproveContractResponse)
async def approve_contract(contract_id: str, session: AsyncSession = Depends(get_session)) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Contract is '{contract.status}', not Pending")
    if await _contract_approval_steps(session, contract_id):
        raise HTTPException(status_code=400, detail="This contract has a configured approval chain — use /advance-step instead")

    summary = _activate_contract(contract)
    log_activity(session, entity_type="contract", entity_id=contract_id, action="approved", contract_id=contract_id, summary=summary)
    await session.commit()
    return ApproveContractResponse(id=contract.id, status=contract.status, oracle_po=contract.oracle_po, oracle_po_rev=contract.oracle_po_rev)


@router.post("/{contract_id}/advance-step", response_model=ApproveContractResponse)
async def advance_contract_step(contract_id: str, session: AsyncSession = Depends(get_session)) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    steps = await _contract_approval_steps(session, contract_id)
    if not steps:
        raise HTTPException(status_code=400, detail="No approval chain configured for this contract — use /approve instead")
    current_idx = next((idx for idx, s in enumerate(steps) if s.state == "current"), None)
    if current_idx is None:
        raise HTTPException(status_code=400, detail="No current step to advance")

    steps[current_idx].state = "done"
    steps[current_idx].meta_note = "Completed"
    completed_role = steps[current_idx].role
    if current_idx + 1 < len(steps):
        steps[current_idx + 1].state = "current"
        steps[current_idx + 1].meta_note = "Awaiting approval"
        summary = f"Contract {contract_id} — step '{completed_role}' completed, now awaiting '{steps[current_idx + 1].role}'"
    else:
        summary = _activate_contract(contract)

    log_activity(session, entity_type="contract", entity_id=contract_id, action="step_advanced", contract_id=contract_id, summary=summary)
    await session.commit()
    return ApproveContractResponse(id=contract.id, status=contract.status, oracle_po=contract.oracle_po, oracle_po_rev=contract.oracle_po_rev)


@router.get("/{contract_id}/tracking", response_model=TrackingResponse)
async def contract_tracking(contract_id: str, session: AsyncSession = Depends(get_session)) -> TrackingResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.contract_type != "scope":
        raise HTTPException(status_code=400, detail="Manpower Supply contracts use /manpower-summary, not IPC tracking")

    result = await session.execute(select(Ipc).where(Ipc.contract_id == contract_id).order_by(Ipc.id))
    ipcs = result.scalars().all()

    retention_held = sum((i.retention for i in ipcs), Decimal("0"))
    retention_released = Decimal("0")
    advance_recovered = sum((i.advance_recovered for i in ipcs), Decimal("0"))
    advance_outstanding = contract.advance_amount - advance_recovered
    net_certified = sum((i.net_payable for i in ipcs), Decimal("0"))
    paid = sum((i.net_payable for i in ipcs if i.status == "Paid"), Decimal("0"))
    remaining_payable = net_certified - paid
    executed_to_date = net_certified
    remaining_value = contract.contract_value - executed_to_date

    def pct(numerator: Decimal, denominator: Decimal) -> str:
        if denominator == 0:
            return "0%"
        return f"{round(float(numerator / denominator) * 100)}%"

    header = TrackingHeader(
        id=contract.id, vendor=contract.vendor_name, type=contract.service_type, project=contract.project_name,
        status=contract.status, progress=f"{contract.progress_pct}%", progressColor=progress_color(contract.progress_pct),
        remainMonths=f"{contract.remaining_months} mo",
        expiry=contract.expiry_date.strftime("%d %b %Y") if contract.expiry_date else "—",
        po=contract.oracle_po, poRev=contract.oracle_po_rev, pr=contract.source_pr,
    )
    finance = [
        FinanceCard(label="Contract Value", value=money(contract.contract_value), note=f"Budget {money(contract.contract_budget)}", color="#667085"),
        FinanceCard(label="Executed to Date", value=money(executed_to_date), note=pct(executed_to_date, contract.contract_value) + " committed", color="#12805c"),
        FinanceCard(
            label="Payment Due", value=money(remaining_payable),
            note="certified, awaiting payment" if remaining_payable > 0 else "fully settled",
            color="#b45309" if remaining_payable > 0 else "#12805c",
        ),
        FinanceCard(label="Remaining", value=money(remaining_value), note="uncommitted", color="#667085"),
        FinanceCard(label="Penalties Applied", value=money(Decimal("0")), note="none this contract", color="#c0362c"),
    ]
    trackers = [
        TrackerCard(
            title="Retention", sub=f"{contract.retention_pct}% held", barW=pct(retention_released, retention_held), barColor="#b45309",
            rows=[
                TrackerRow(k="Held to date", v=money(retention_held), w=600, c="#101828"),
                TrackerRow(k="Released", v=money(retention_released), w=500, c="#667085"),
                TrackerRow(k="Remaining held", v=money(retention_held - retention_released), w=500, c="#b45309"),
            ],
        ),
        TrackerCard(
            title="Advance Recovery", sub=f"{pct(advance_recovered, contract.advance_amount)} recovered", barW=pct(advance_recovered, contract.advance_amount), barColor="#2c7fb0",
            rows=[
                TrackerRow(k="Advance paid", v=money(contract.advance_amount), w=600, c="#101828"),
                TrackerRow(k="Recovered", v=money(advance_recovered), w=500, c="#12805c"),
                TrackerRow(k="Outstanding", v=money(advance_outstanding), w=500, c="#2c7fb0"),
            ],
        ),
        TrackerCard(
            title="Payable Status", sub=f"{pct(paid, net_certified)} paid", barW=pct(paid, net_certified), barColor="#12805c",
            rows=[
                TrackerRow(k="Net certified", v=money(net_certified), w=600, c="#101828"),
                TrackerRow(k="Paid", v=money(paid), w=500, c="#12805c"),
                TrackerRow(k="Remaining", v=money(remaining_payable), w=500, c="#b45309"),
            ],
        ),
    ]
    ipc_rows = [
        IpcRow(
            id=i.id, n=i.number, period=i.period, done=f"{i.work_done_pct}%", gross=fmt_num(i.gross), ret=fmt_num(i.retention),
            adv=fmt_num(i.advance_recovered), net=fmt_num(i.net_payable), status=i.status,
            color="#12805c" if i.status == "Paid" else "#3a5bd9", bg="#e6f4ee" if i.status == "Paid" else "#eef1fd",
        )
        for i in ipcs
    ]
    return TrackingResponse(header=header, finance=finance, trackers=trackers, ipcs=ipc_rows)


async def _build_ipc(session: AsyncSession, contract: Contract, period: str, work_done_pct: Decimal, gross: Decimal) -> Ipc:
    result = await session.execute(select(Ipc).where(Ipc.contract_id == contract.id).order_by(Ipc.id))
    existing = result.scalars().all()
    already_recovered = sum((i.advance_recovered for i in existing), Decimal("0"))
    remaining_advance = max(Decimal("0"), contract.advance_amount - already_recovered)

    retention = (gross * contract.retention_pct / Decimal("100")).quantize(Decimal("0.01"))
    proposed_advance_recovery = (gross * contract.advance_pct / Decimal("100")).quantize(Decimal("0.01"))
    advance_recovered = min(proposed_advance_recovery, remaining_advance)
    net_payable = gross - retention - advance_recovered

    ipc = Ipc(
        contract_id=contract.id,
        number=f"IPC {len(existing) + 1}",
        period=period,
        work_done_pct=work_done_pct,
        gross=gross,
        retention=retention,
        advance_recovered=advance_recovered,
        net_payable=net_payable,
        status="Certifying",
    )
    session.add(ipc)
    contract.progress_pct = int(work_done_pct)
    return ipc


def _ipc_row(ipc: Ipc) -> IpcRow:
    return IpcRow(
        id=ipc.id, n=ipc.number, period=ipc.period, done=f"{ipc.work_done_pct}%", gross=fmt_num(ipc.gross), ret=fmt_num(ipc.retention),
        adv=fmt_num(ipc.advance_recovered), net=fmt_num(ipc.net_payable), status=ipc.status, color="#3a5bd9", bg="#eef1fd",
    )


@router.post("/{contract_id}/ipcs", response_model=IpcRow, status_code=201)
async def create_ipc(contract_id: str, payload: IpcCreateRequest, session: AsyncSession = Depends(get_session)) -> IpcRow:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    ipc = await _build_ipc(session, contract, payload.period, Decimal(str(payload.workDonePct)), Decimal(str(payload.gross)))
    log_activity(
        session, entity_type="ipc", entity_id=ipc.number, action="created", contract_id=contract_id,
        summary=f"{ipc.number} created for {contract_id} — {ipc.period}, {ipc.work_done_pct}% complete, net payable {money(ipc.net_payable)}",
    )
    await session.commit()
    await session.refresh(ipc)
    return _ipc_row(ipc)


@router.get("/{contract_id}/ipcs/{ipc_id}/certificate", response_model=IpcCertificateResponse)
async def ipc_certificate(contract_id: str, ipc_id: int, session: AsyncSession = Depends(get_session)) -> IpcCertificateResponse:
    """Full IPC certificate document - downloadable/printable, handed to the contractor as proof of certified payment."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    ipc = await session.get(Ipc, ipc_id)
    if not ipc or ipc.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="IPC not found")

    return IpcCertificateResponse(
        contractId=contract.id,
        vendor=contract.vendor_name,
        contractorNo=contract.contractor_no,
        project=contract.project_name,
        projectNo=contract.project_no,
        oraclePo=contract.oracle_po,
        oraclePoRev=contract.oracle_po_rev,
        ipcNumber=ipc.number,
        period=ipc.period,
        workDonePct=f"{ipc.work_done_pct}%",
        gross=money(ipc.gross),
        retentionPct=f"{contract.retention_pct}%",
        retention=money(ipc.retention),
        advanceRecovered=money(ipc.advance_recovered),
        netPayable=money(ipc.net_payable),
        payableTermsDays=f"{contract.payable_terms_days} days",
        status=ipc.status,
        createdAt=ipc.created_at.strftime("%d %b %Y"),
    )


@router.get("/{contract_id}/vendor-submissions", response_model=list[VendorSubmissionOut])
async def list_vendor_submissions(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[VendorSubmissionOut]:
    """Subcontractor progress claims from the Oracle vendor portal, awaiting PMO certification into an IPC."""
    result = await session.execute(
        select(VendorPortalSubmission).where(VendorPortalSubmission.contract_id == contract_id).order_by(VendorPortalSubmission.submitted_at)
    )
    return [
        VendorSubmissionOut(
            id=s.id, period=s.period, workDonePct=f"{s.work_done_pct}%", grossClaimed=money(s.gross_claimed),
            submittedBy=s.submitted_by, submittedAt=s.submitted_at.strftime("%d %b %Y"), status=s.status,
        )
        for s in result.scalars().all()
    ]


@router.post("/{contract_id}/vendor-submissions/{submission_id}/certify", response_model=IpcRow, status_code=201)
async def certify_vendor_submission(contract_id: str, submission_id: int, session: AsyncSession = Depends(get_session)) -> IpcRow:
    """Certifies a vendor portal work-progress claim into an actual IPC."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    submission = await session.get(VendorPortalSubmission, submission_id)
    if not submission or submission.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="Vendor submission not found")
    if submission.status != "Submitted":
        raise HTTPException(status_code=400, detail=f"Submission is already '{submission.status}'")

    ipc = await _build_ipc(session, contract, submission.period, submission.work_done_pct, submission.gross_claimed)
    submission.status = "Certified"
    log_activity(
        session, entity_type="ipc", entity_id=ipc.number, action="certified", contract_id=contract_id,
        summary=f"Vendor portal submission for {submission.period} certified into {ipc.number} — {contract_id}, {submission.work_done_pct}% complete",
    )
    await session.commit()
    await session.refresh(ipc)
    return _ipc_row(ipc)


@router.get("/{contract_id}/summary", response_model=ContractSummaryDocResponse)
async def contract_summary_document(contract_id: str, session: AsyncSession = Depends(get_session)) -> ContractSummaryDocResponse:
    """Full contract document backing the downloadable/printable summary page."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    result = await session.execute(select(ContractLineItem).where(ContractLineItem.contract_id == contract_id).order_by(ContractLineItem.id))
    line_items = result.scalars().all()

    return ContractSummaryDocResponse(
        id=contract.id,
        vendor=contract.vendor_name,
        contractorNo=contract.contractor_no,
        serviceType=contract.service_type,
        project=contract.project_name,
        projectNo=contract.project_no,
        durationMonths=contract.duration_months,
        contractValue=money(contract.contract_value),
        contractBudget=money(contract.contract_budget),
        retentionPct=f"{contract.retention_pct}%",
        advancePct=f"{contract.advance_pct}%",
        payableTermsDays=f"{contract.payable_terms_days} days",
        sourcePr=contract.source_pr,
        oraclePo=contract.oracle_po,
        oraclePoRev=contract.oracle_po_rev,
        status=contract.status,
        createdAt=contract.created_at.strftime("%d %b %Y"),
        lineItems=[
            SummaryLineItemOut(
                code=li.code, prLineRef=li.pr_line_ref, description=li.description, qty=fmt_num(li.qty), uom=li.uom,
                unitRate=money(li.unit_rate), budget=money(li.budget), total=money(li.total), slaTags=split_tags(li.sla_tags),
                previousQty=fmt_num(li.previous_qty) if li.previous_qty is not None else None,
                revisedByCo=li.revised_by_co,
            )
            for li in line_items
        ],
    )
