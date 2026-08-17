import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.approval_actions import apply_decision, apply_revision, steps_to_out
from app.auth import assert_contract_visible, get_current_user, require_roles
from app.business import fmt_num, join_tags, money, progress_color, split_tags, status_colors, type_colors
from app.database import get_session
from app.email_service import attachments_for_email, send_workflow_notification
from app.models import (
    ApprovalStep,
    AppUser,
    Contract,
    ContractLineItem,
    GrnLine,
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
    WorkflowTemplate,
)
from app.schemas.attachments import AttachmentOut
from app.schemas.change_orders import ApprovalStepOut, DecisionRequest, ReviseDecisionRequest
from app.storage import claim_attachments, get_owner_attachments, require_attachment
from app.workflow_engine import resolve_chain, seed_approval_steps
from app.schemas.contracts import (
    ApprovalFlowInfo,
    ApproveContractResponse,
    ContractListResponse,
    ContractorOptionOut,
    ContractSummary,
    ContractSummaryDocResponse,
    DraftLineItem,
    FinanceCard,
    IpcCertificateResponse,
    IpcCreateRequest,
    IpcGrnInvoiceResponse,
    IpcGrnInvoiceTotals,
    IpcGrnLineOut,
    IpcInvoiceAdvanceStatement,
    IpcInvoiceDeductionRow,
    IpcInvoiceResponse,
    IpcInvoiceRetentionStatement,
    IpcInvoiceTotals,
    IpcReportAdvanceTracker,
    IpcReportLineOut,
    IpcReportResponse,
    IpcReportRetentionTracker,
    IpcReportTotals,
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
    current_user: AppUser = Depends(get_current_user),
) -> ContractListResponse:
    stmt = select(Contract)
    if current_user.role == "procurement_requester":
        stmt = stmt.where(Contract.contract_type == "scope")
    elif current_user.role == "hr_requester":
        stmt = stmt.where(Contract.contract_type == "manpower")
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


@router.get("/oracle-projects", response_model=list[ProjectOptionOut])
async def list_oracle_projects_with_prs(session: AsyncSession = Depends(get_session)) -> list[ProjectOptionOut]:
    """Projects that have at least one approved Oracle PR available to draft a Scope/Works
    contract from - the picker shown before the PR picker, so the user narrows by project first.
    """
    result = await session.execute(select(OraclePr.project_no, OraclePr.project_name).distinct().order_by(OraclePr.project_name))
    return [ProjectOptionOut(projectNo=row.project_no, projectName=row.project_name) for row in result.all()]


@router.get("/oracle-prs", response_model=list[OraclePrOptionOut])
async def list_oracle_prs(project: str | None = None, session: AsyncSession = Depends(get_session)) -> list[OraclePrOptionOut]:
    """Approved Oracle PRs available to draft a Scope/Works contract from - the picker shown
    before the BOQ draft screen, instead of always auto-selecting the first PR in the feed.
    Optionally filtered to a single project, once the user has selected one from the project picker.
    """
    stmt = select(OraclePr).order_by(OraclePr.id)
    if project:
        stmt = stmt.where(OraclePr.project_no == project)
    result = await session.execute(stmt)
    return [
        OraclePrOptionOut(
            id=pr.id, vendorName=pr.vendor_name, projectName=pr.project_name, projectNo=pr.project_no,
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


@router.post("", response_model=ContractSummary, status_code=201, dependencies=[Depends(require_roles("admin", "procurement_requester"))])
async def create_contract(
    payload: NewContractRequest, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> ContractSummary:
    await require_attachment(session, payload.draftToken)
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
        created_by_id=current_user.id,
    )
    session.add(contract)
    for li in payload.lineItems:
        session.add(ContractLineItem(
            contract_id=new_id, code=li.code, pr_line_ref=li.prLineRef, description=li.description,
            qty=Decimal(str(li.qty)), uom=li.uom, unit_rate=Decimal(str(li.unitRate)),
            budget=Decimal(str(li.budget)), total=Decimal(str(li.qty)) * Decimal(str(li.unitRate)),
            sla_tags=join_tags(li.slaTags),
        ))
    await seed_approval_steps(
        session, owner_type="contract", owner_id=new_id, applies_to="contract_scope",
        fallback_template=[], raiser_name="Submitted by Contract Owner",
    )
    await claim_attachments(session, payload.draftToken, "contract", new_id)

    log_activity(
        session, entity_type="contract", entity_id=new_id, action="created", contract_id=new_id,
        summary=f"Contract {new_id} created for {payload.vendorName} — {payload.projectName} ({payload.serviceType}), value {money(Decimal(str(payload.contractValue)))}",
    )
    await session.commit()
    await session.refresh(contract)
    await _notify_current_step(session, contract, await _contract_approval_steps(session, new_id))
    return _summary(contract)


def _position_line_total_cost(li) -> Decimal:
    return (
        Decimal(str(li.basicSalary)) + Decimal(str(li.hAllowance)) + Decimal(str(li.tAllowance))
        + Decimal(str(li.fAllowance)) + Decimal(str(li.share))
    )


@router.post("/manpower", response_model=ContractSummary, status_code=201, dependencies=[Depends(require_roles("admin", "hr_requester"))])
async def create_manpower_contract(
    payload: NewManpowerContractRequest, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> ContractSummary:
    """Manpower Supply contracts are created without an Oracle PR - no BOQ, no retention/advance,
    a rate-card (position lines) instead. Kept as a separate endpoint from Scope/Works so the two
    flows never share validation rules, per CLAUDE.md's domain rules.
    """
    if not payload.positionLines:
        raise HTTPException(status_code=400, detail="At least one position line is required")
    await require_attachment(session, payload.draftToken)

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
        created_by_id=current_user.id,
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
    await seed_approval_steps(
        session, owner_type="contract", owner_id=new_id, applies_to="contract_manpower",
        fallback_template=[], raiser_name="Submitted by Contract Owner",
    )
    await claim_attachments(session, payload.draftToken, "contract", new_id)

    log_activity(
        session, entity_type="contract", entity_id=new_id, action="created", contract_id=new_id,
        summary=f"Manpower Supply contract {new_id} created for {payload.vendorName}, value {money(contract_value)}",
    )
    await session.commit()
    await session.refresh(contract)
    await _notify_current_step(session, contract, await _contract_approval_steps(session, new_id))
    return _summary(contract)


@router.get("/{contract_id}/manpower-summary", response_model=ManpowerContractSummaryResponse)
async def manpower_contract_summary(
    contract_id: str, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> ManpowerContractSummaryResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.contract_type != "manpower":
        raise HTTPException(status_code=400, detail="Not a Manpower Supply contract")
    assert_contract_visible(current_user, contract)

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
        # Real Oracle PO creation carries the contract number in the PO's Descriptive Flexfield
        # (DFF) - that's how a PO gets traced back to the subcontract that spawned it. Not
        # modeled as a separate column here since the DFF itself lives in Oracle, not this system;
        # _po_dff_ref() below derives the same value for display.
        return (
            f"Contract {contract.id} approved — Oracle PO {contract.oracle_po} ({contract.oracle_po_rev}) created for "
            f"{contract.vendor_name}, with contract no. {contract.id} written into the PO's DFF for traceability"
        )
    return f"Manpower Supply contract {contract.id} approved for {contract.vendor_name}"


def _po_dff_ref(contract: Contract) -> str | None:
    """The value carried in the Oracle PO's Descriptive Flexfield - the contract number, once a
    PO exists for this contract. Derived, not stored - see _activate_contract() above."""
    return contract.id if contract.oracle_po else None


@router.get("/{contract_id}/approval-steps", response_model=list[ApprovalStepOut])
async def get_contract_approval_steps(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[ApprovalStepOut]:
    """Empty unless an admin has built and activated a Contract approval flow in /approval-flows —
    otherwise contracts use the plain one-shot /approve below, same as before that feature existed.
    """
    steps = await _contract_approval_steps(session, contract_id)
    return await steps_to_out(session, steps)


@router.get("/{contract_id}/approval-flow", response_model=ApprovalFlowInfo)
async def get_contract_approval_flow(contract_id: str, session: AsyncSession = Depends(get_session)) -> ApprovalFlowInfo:
    """Name of the WorkflowTemplate that was active (and so governs this contract's approval
    chain) - None if the chain came from the fallback (no flow ever configured/activated).
    """
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    applies_to = "contract_scope" if contract.contract_type == "scope" else "contract_manpower"
    active = await session.scalar(
        select(WorkflowTemplate).where(WorkflowTemplate.applies_to == applies_to, WorkflowTemplate.is_active == True)  # noqa: E712
    )
    return ApprovalFlowInfo(workflowName=active.name if active else None)


async def _notify_current_step(session: AsyncSession, contract: Contract, steps: list[ApprovalStep]) -> None:
    current = next((s for s in steps if s.state == "current"), None)
    if not current or not current.approver_user_id:
        return
    approver = await session.get(AppUser, current.approver_user_id)
    if not approver:
        return
    attachments = await get_owner_attachments(session, "contract", contract.id)
    await send_workflow_notification(
        to_email=approver.email, to_name=approver.name, heading=f"Awaiting your approval — {contract.id}",
        owner_type="contract", owner_id=contract.id,
        rows=[("Vendor", contract.vendor_name), ("Value", money(contract.contract_value)), ("Your role", current.role)],
        link_path=f"/contracts/{contract.id}", attachments=attachments_for_email(attachments),
    )


async def _notify_requester(session: AsyncSession, contract: Contract, heading: str, extra_rows: list[tuple[str, str]]) -> None:
    if not contract.created_by_id:
        return
    requester = await session.get(AppUser, contract.created_by_id)
    if not requester:
        return
    attachments = await get_owner_attachments(session, "contract", contract.id)
    await send_workflow_notification(
        to_email=requester.email, to_name=requester.name, heading=heading, owner_type="contract", owner_id=contract.id,
        rows=[("Vendor", contract.vendor_name), ("Value", money(contract.contract_value)), *extra_rows],
        link_path=f"/contracts/{contract.id}", attachments=attachments_for_email(attachments),
    )


@router.get("/{contract_id}/attachments", response_model=list[AttachmentOut])
async def get_contract_attachments(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[AttachmentOut]:
    return [
        AttachmentOut(id=a.id, filename=a.filename, contentType=a.content_type, sizeBytes=a.size_bytes, uploadedAt=a.uploaded_at.strftime("%d %b %Y %H:%M"))
        for a in await get_owner_attachments(session, "contract", contract_id)
    ]


@router.post("/{contract_id}/approve", response_model=ApproveContractResponse, dependencies=[Depends(require_roles("admin", "approver"))])
async def approve_contract(contract_id: str, session: AsyncSession = Depends(get_session)) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Contract is '{contract.status}', not Pending")
    if await _contract_approval_steps(session, contract_id):
        raise HTTPException(status_code=400, detail="This contract has a configured approval chain — use /decide instead")

    summary = _activate_contract(contract)
    log_activity(session, entity_type="contract", entity_id=contract_id, action="approved", contract_id=contract_id, summary=summary)
    await session.commit()
    await _notify_requester(session, contract, f"Contract {contract.id} was approved", [("Oracle PO", contract.oracle_po or "—")])
    return ApproveContractResponse(
        id=contract.id, status=contract.status, oracle_po=contract.oracle_po,
        oracle_po_rev=contract.oracle_po_rev, oracle_po_dff_ref=_po_dff_ref(contract),
    )


@router.post("/{contract_id}/reject", response_model=ApproveContractResponse, dependencies=[Depends(require_roles("admin", "approver"))])
async def reject_contract(contract_id: str, session: AsyncSession = Depends(get_session)) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Contract is '{contract.status}', not Pending")
    if await _contract_approval_steps(session, contract_id):
        raise HTTPException(status_code=400, detail="This contract has a configured approval chain — use /decide instead")

    contract.status = "Rejected"
    summary = f"Contract {contract_id} rejected"
    log_activity(session, entity_type="contract", entity_id=contract_id, action="rejected", contract_id=contract_id, summary=summary)
    await session.commit()
    await _notify_requester(session, contract, f"Contract {contract.id} was rejected", [])
    return ApproveContractResponse(
        id=contract.id, status=contract.status, oracle_po=contract.oracle_po,
        oracle_po_rev=contract.oracle_po_rev, oracle_po_dff_ref=_po_dff_ref(contract),
    )


@router.post("/{contract_id}/decide", response_model=ApproveContractResponse)
async def decide_contract_step(
    contract_id: str, payload: DecisionRequest, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    steps = await _contract_approval_steps(session, contract_id)
    if not steps:
        raise HTTPException(status_code=400, detail="No approval chain configured for this contract — use /approve or /reject instead")

    result = apply_decision(steps, current_user, payload.decision, payload.comment)
    if result.result == "rejected":
        contract.status = "Rejected"
        summary = f"Contract {contract_id} rejected at step '{result.step.role}' by {current_user.name}"
        await _notify_requester(session, contract, f"Contract {contract.id} was rejected", [("Rejected by", current_user.name), ("Comment", payload.comment or "—")])
    elif result.result == "completed":
        summary = _activate_contract(contract)
        await _notify_requester(session, contract, f"Contract {contract.id} was approved", [("Oracle PO", contract.oracle_po or "—")])
    else:
        summary = f"Contract {contract_id} — step '{result.step.role}' {payload.decision} by {current_user.name}, now awaiting '{result.next_step.role}'"
        await _notify_current_step(session, contract, steps)

    log_activity(session, entity_type="contract", entity_id=contract_id, action="step_decided", contract_id=contract_id, summary=summary)
    await session.commit()
    return ApproveContractResponse(
        id=contract.id, status=contract.status, oracle_po=contract.oracle_po,
        oracle_po_rev=contract.oracle_po_rev, oracle_po_dff_ref=_po_dff_ref(contract),
    )


@router.post("/{contract_id}/steps/{step_id}/revise", response_model=ApproveContractResponse)
async def revise_contract_step(
    contract_id: str, step_id: int, payload: ReviseDecisionRequest, session: AsyncSession = Depends(get_session),
    current_user: AppUser = Depends(get_current_user),
) -> ApproveContractResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    steps = await _contract_approval_steps(session, contract_id)
    step = next((s for s in steps if s.id == step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail="Approval step not found")

    result = apply_revision(steps, step, current_user, payload.decision, payload.reason, session)
    if result.result == "rejected":
        contract.status = "Rejected"
        summary = f"Contract {contract_id} — step '{result.step.role}' revised to rejected by {current_user.name} ({payload.reason})"
    elif result.result == "completed":
        summary = _activate_contract(contract)
        await _notify_requester(session, contract, f"Contract {contract.id} was approved", [("Oracle PO", contract.oracle_po or "—")])
    else:
        contract.status = "Pending"
        summary = f"Contract {contract_id} — step '{result.step.role}' revised to {payload.decision} by {current_user.name} ({payload.reason})"
        await _notify_current_step(session, contract, steps)

    await _notify_requester(session, contract, f"A decision on contract {contract.id} was revised", [("Revised by", current_user.name), ("New decision", payload.decision), ("Reason", payload.reason)])
    log_activity(session, entity_type="contract", entity_id=contract_id, action="step_revised", contract_id=contract_id, summary=summary)
    await session.commit()
    return ApproveContractResponse(
        id=contract.id, status=contract.status, oracle_po=contract.oracle_po,
        oracle_po_rev=contract.oracle_po_rev, oracle_po_dff_ref=_po_dff_ref(contract),
    )


@router.get("/{contract_id}/tracking", response_model=TrackingResponse)
async def contract_tracking(
    contract_id: str, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> TrackingResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.contract_type != "scope":
        raise HTTPException(status_code=400, detail="Manpower Supply contracts use /manpower-summary, not IPC tracking")
    assert_contract_visible(current_user, contract)

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
        po=contract.oracle_po, poRev=contract.oracle_po_rev, poDffRef=_po_dff_ref(contract), pr=contract.source_pr,
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
            oraclePushStatus=i.oracle_push_status, oracleConfirmationCode=i.oracle_confirmation_code,
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
        oraclePushStatus=ipc.oracle_push_status, oracleConfirmationCode=ipc.oracle_confirmation_code,
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


@router.get("/{contract_id}/ipcs/{ipc_id}/report", response_model=IpcReportResponse)
async def ipc_report(contract_id: str, ipc_id: int, session: AsyncSession = Depends(get_session)) -> IpcReportResponse:
    """BOQ-level progress payment report for one IPC - apportions the IPC's certified gross amount
    across BOQ line items (pro-rata to each line's share of the contract BOQ total) to show Previous /
    Current / Total executed qty and amount per line, for internal PMO/QS review."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    ipc = await session.get(Ipc, ipc_id)
    if not ipc or ipc.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="IPC not found")

    ipcs_result = await session.execute(select(Ipc).where(Ipc.contract_id == contract_id).order_by(Ipc.id))
    all_ipcs = ipcs_result.scalars().all()
    prior_ipcs = [i for i in all_ipcs if i.id < ipc.id]

    gross_before = sum((i.gross for i in prior_ipcs), Decimal("0"))
    retention_before = sum((i.retention for i in prior_ipcs), Decimal("0"))
    advance_before = sum((i.advance_recovered for i in prior_ipcs), Decimal("0"))
    gross_upto = gross_before + ipc.gross
    retention_upto = retention_before + ipc.retention
    advance_upto = advance_before + ipc.advance_recovered

    lines_result = await session.execute(
        select(ContractLineItem).where(ContractLineItem.contract_id == contract_id).order_by(ContractLineItem.id)
    )
    line_items = lines_result.scalars().all()
    boq_total = sum((li.total for li in line_items), Decimal("0"))

    line_rows: list[IpcReportLineOut] = []
    for li in line_items:
        weight = (li.total / boq_total) if boq_total else Decimal("0")
        previous_amount = (gross_before * weight).quantize(Decimal("0.01"))
        current_amount = (ipc.gross * weight).quantize(Decimal("0.01"))
        total_amount = previous_amount + current_amount
        previous_qty = (previous_amount / li.unit_rate) if li.unit_rate else Decimal("0")
        current_qty = (current_amount / li.unit_rate) if li.unit_rate else Decimal("0")
        total_qty = previous_qty + current_qty
        line_rows.append(
            IpcReportLineOut(
                code=li.code, prLineRef=li.pr_line_ref, description=li.description, uom=li.uom,
                contractQty=fmt_num(li.qty), unitRate=money(li.unit_rate), contractTotal=money(li.total),
                previousQty=fmt_num(previous_qty), previousAmount=money(previous_amount),
                currentQty=fmt_num(current_qty), currentAmount=money(current_amount),
                totalQty=fmt_num(total_qty), totalAmount=money(total_amount),
            )
        )

    totals = IpcReportTotals(
        boqGrossTotal=money(boq_total),
        previousAmountTotal=money(gross_before),
        currentAmountTotal=money(ipc.gross),
        totalExecutedToDate=money(gross_upto),
        retentionPct=f"{contract.retention_pct}%",
        retentionCurrent=money(ipc.retention),
        retentionToDate=money(retention_upto),
        advancePct=f"{contract.advance_pct}%",
        advanceRecoveredCurrent=money(ipc.advance_recovered),
        advanceRecoveredToDate=money(advance_upto),
        netPayableCurrent=money(ipc.net_payable),
        netPayableToDate=money(gross_upto - retention_upto - advance_upto),
    )
    advance_tracker = IpcReportAdvanceTracker(
        advancePaid=money(contract.advance_amount),
        advanceRecoveredToDate=money(advance_upto),
        outstandingAdvance=money(contract.advance_amount - advance_upto),
    )
    retention_tracker = IpcReportRetentionTracker(
        retentionHeldToDate=money(retention_upto),
        retentionReleased=money(Decimal("0")),
        netRetention=money(retention_upto),
    )

    return IpcReportResponse(
        contractId=contract.id, vendor=contract.vendor_name, contractorNo=contract.contractor_no,
        project=contract.project_name, projectNo=contract.project_no, oraclePo=contract.oracle_po,
        oraclePoRev=contract.oracle_po_rev, sourcePr=contract.source_pr, ipcNumber=ipc.number,
        period=ipc.period, status=ipc.status, createdAt=ipc.created_at.strftime("%d %b %Y"),
        lines=line_rows, totals=totals, advanceTracker=advance_tracker, retentionTracker=retention_tracker,
    )


def _capped_recovery_series(gross_series: list[Decimal], pct: Decimal, pool_amount: Decimal) -> list[Decimal]:
    """Replays the same capped pro-rata recovery logic _build_ipc uses for the (stored) primary
    advance tranche, against an arbitrary sequence of period-gross figures - used both for tranches/LC
    pools that aren't persisted per IPC, and for the GRN-verified gross series (ipc_grn_invoice)."""
    recovered: list[Decimal] = []
    already = Decimal("0")
    for gross in gross_series:
        remaining = max(Decimal("0"), pool_amount - already)
        proposed = (gross * pct / Decimal("100")).quantize(Decimal("0.01"))
        take = min(proposed, remaining)
        recovered.append(take)
        already += take
    return recovered


def _tranche_recovery_series(ipcs_in_order: list[Ipc], pct: Decimal, pool_amount: Decimal) -> list[Decimal]:
    return _capped_recovery_series([i.gross for i in ipcs_in_order], pct, pool_amount)


def _grn_cumulative(entries: list[GrnLine], cutoff: datetime.date | None) -> Decimal:
    """Sum of GRN quantities received on or before `cutoff`. cutoff=None means "before anything has
    been received yet" (used as the lower bound when there is no prior IPC period)."""
    if cutoff is None:
        return Decimal("0")
    return sum((g.qty_received for g in entries if g.received_date <= cutoff), Decimal("0"))


@router.get("/{contract_id}/ipcs/{ipc_id}/invoice", response_model=IpcInvoiceResponse)
async def ipc_invoice(contract_id: str, ipc_id: int, session: AsyncSession = Depends(get_session)) -> IpcInvoiceResponse:
    """Full vendor invoice / payment certificate document for one IPC - mirrors the subcontractor's
    own Excel invoice workbook: BOQ execution breakdown plus VAT, dual advance-tranche recovery,
    equipment rental deduction, and a letter-of-credit tracker. Verified formula:
    Net Amount (current) = Gross(current) + VAT(current) - Retention(current) - Advance Tranche 1(current)
    - Advance Tranche 2(current) - Letter of Credit(current) - Equipment Rental(current)."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    ipc = await session.get(Ipc, ipc_id)
    if not ipc or ipc.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="IPC not found")

    ipcs_result = await session.execute(select(Ipc).where(Ipc.contract_id == contract_id).order_by(Ipc.id))
    all_ipcs = ipcs_result.scalars().all()
    prior_ipcs = [i for i in all_ipcs if i.id < ipc.id]
    ipcs_upto = prior_ipcs + [ipc]

    gross_before = sum((i.gross for i in prior_ipcs), Decimal("0"))
    gross_upto = gross_before + ipc.gross
    retention_before = sum((i.retention for i in prior_ipcs), Decimal("0"))
    retention_upto = retention_before + ipc.retention
    adv1_before = sum((i.advance_recovered for i in prior_ipcs), Decimal("0"))
    adv1_upto = adv1_before + ipc.advance_recovered
    equipment_before = sum((i.equipment_rental_deduction for i in prior_ipcs), Decimal("0"))
    equipment_current = ipc.equipment_rental_deduction
    equipment_upto = equipment_before + equipment_current

    vat_before = (gross_before * contract.vat_pct / Decimal("100")).quantize(Decimal("0.01"))
    vat_current = (ipc.gross * contract.vat_pct / Decimal("100")).quantize(Decimal("0.01"))
    vat_upto = vat_before + vat_current

    adv2_series = _tranche_recovery_series(ipcs_upto, contract.advance2_pct, contract.advance2_amount)
    adv2_before, adv2_current = sum(adv2_series[:-1], Decimal("0")), adv2_series[-1]
    adv2_upto = adv2_before + adv2_current

    lc_series = _tranche_recovery_series(ipcs_upto, contract.lc_pct, contract.lc_amount)
    lc_before, lc_current = sum(lc_series[:-1], Decimal("0")), lc_series[-1]
    lc_upto = lc_before + lc_current

    total_deduction_before = retention_before + adv1_before + adv2_before + lc_before + equipment_before
    total_deduction_current = ipc.retention + ipc.advance_recovered + adv2_current + lc_current + equipment_current
    total_deduction_upto = total_deduction_before + total_deduction_current

    previous_net_paid = (gross_before + vat_before) - total_deduction_before
    net_amount_current = (ipc.gross + vat_current) - total_deduction_current

    lines_result = await session.execute(
        select(ContractLineItem).where(ContractLineItem.contract_id == contract_id).order_by(ContractLineItem.id)
    )
    line_items = lines_result.scalars().all()
    boq_total = sum((li.total for li in line_items), Decimal("0"))

    line_rows: list[IpcReportLineOut] = []
    for li in line_items:
        weight = (li.total / boq_total) if boq_total else Decimal("0")
        previous_amount = (gross_before * weight).quantize(Decimal("0.01"))
        current_amount = (ipc.gross * weight).quantize(Decimal("0.01"))
        total_amount = previous_amount + current_amount
        previous_qty = (previous_amount / li.unit_rate) if li.unit_rate else Decimal("0")
        current_qty = (current_amount / li.unit_rate) if li.unit_rate else Decimal("0")
        total_qty = previous_qty + current_qty
        line_rows.append(
            IpcReportLineOut(
                code=li.code, prLineRef=li.pr_line_ref, description=li.description, uom=li.uom,
                contractQty=fmt_num(li.qty), unitRate=money(li.unit_rate), contractTotal=money(li.total),
                previousQty=fmt_num(previous_qty), previousAmount=money(previous_amount),
                currentQty=fmt_num(current_qty), currentAmount=money(current_amount),
                totalQty=fmt_num(total_qty), totalAmount=money(total_amount),
            )
        )

    deductions = [
        IpcInvoiceDeductionRow(
            label=f"Retention ({contract.retention_pct}%)", rateLabel=f"{contract.retention_pct}%",
            previous=money(retention_before), current=money(ipc.retention), toDate=money(retention_upto),
        ),
        IpcInvoiceDeductionRow(
            label=f"Advance Recovery — Tranche 1 ({contract.advance_pct}%)", rateLabel=f"{contract.advance_pct}%",
            previous=money(adv1_before), current=money(ipc.advance_recovered), toDate=money(adv1_upto),
        ),
        IpcInvoiceDeductionRow(
            label=f"Advance Recovery — Tranche 2 ({contract.advance2_pct}%)", rateLabel=f"{contract.advance2_pct}%",
            previous=money(adv2_before), current=money(adv2_current), toDate=money(adv2_upto),
        ),
        IpcInvoiceDeductionRow(
            label="Deduction for Equipment Rental", rateLabel="Fixed",
            previous=money(equipment_before), current=money(equipment_current), toDate=money(equipment_upto),
        ),
    ]

    totals = IpcInvoiceTotals(
        boqGrossTotal=money(boq_total),
        previousExecuted=money(gross_before),
        currentExecuted=money(ipc.gross),
        totalExecutedToDate=money(gross_upto),
        vatPreviousTotal=money(vat_before),
        vatCurrentTotal=money(vat_current),
        vatToDateTotal=money(vat_upto),
        totalExecutedInclVatToDate=money(gross_upto + vat_upto),
        deductions=deductions,
        totalDeductionPrevious=money(total_deduction_before),
        totalDeductionCurrent=money(total_deduction_current),
        totalDeductionToDate=money(total_deduction_upto),
        previousNetPaid=money(previous_net_paid),
        netAmountCurrent=money(net_amount_current),
    )

    def _pct_of_contract(amount: Decimal) -> str:
        if contract.contract_value == 0:
            return "0%"
        return f"{round(float(amount / contract.contract_value) * 100, 2)}%"

    advance_statements = [
        IpcInvoiceAdvanceStatement(
            label="Advance Tranche 1", pctOfContract=_pct_of_contract(contract.advance_amount),
            amount=money(contract.advance_amount), recoveredToDate=money(adv1_upto),
            outstanding=money(contract.advance_amount - adv1_upto), applicable=contract.advance_amount > 0,
        ),
        IpcInvoiceAdvanceStatement(
            label="Advance Tranche 2", pctOfContract=_pct_of_contract(contract.advance2_amount),
            amount=money(contract.advance2_amount), recoveredToDate=money(adv2_upto),
            outstanding=money(contract.advance2_amount - adv2_upto), applicable=contract.advance2_amount > 0,
        ),
    ]
    lc_statement = IpcInvoiceAdvanceStatement(
        label="Letter of Credit", pctOfContract=_pct_of_contract(contract.lc_amount),
        amount=money(contract.lc_amount), recoveredToDate=money(lc_upto),
        outstanding=money(contract.lc_amount - lc_upto), applicable=contract.lc_amount > 0,
    )
    retention_statement = IpcInvoiceRetentionStatement(
        pct=f"{contract.retention_pct}%", ofAmount=money(gross_upto),
        heldToDate=money(retention_upto), released=money(Decimal("0")), netRetention=money(retention_upto),
    )

    return IpcInvoiceResponse(
        contractId=contract.id, vendor=contract.vendor_name, project=contract.project_name, projectNo=contract.project_no,
        location=contract.location, refNote=contract.ref_note, erpRef=contract.erp_ref, contractNumber=contract.id,
        invoiceNumber=ipc.invoice_number or ipc.number, date=ipc.created_at.strftime("%d %b %Y"),
        periodFrom=ipc.period_from.strftime("%d-%b-%Y") if ipc.period_from else None,
        periodTo=ipc.period_to.strftime("%d-%b-%Y") if ipc.period_to else None,
        status=ipc.status, lines=line_rows, totals=totals,
        advanceStatements=advance_statements, lcStatement=lc_statement, retentionStatement=retention_statement,
    )


@router.get("/{contract_id}/ipcs/{ipc_id}/grn-invoice", response_model=IpcGrnInvoiceResponse)
async def ipc_grn_invoice(contract_id: str, ipc_id: int, session: AsyncSession = Depends(get_session)) -> IpcGrnInvoiceResponse:
    """Invoice / payment certificate grounded in Goods Receipt Note (GRN) data - actual received
    quantities per BOQ line, logged independently of the vendor's self-declared work-done % - rather
    than the certified IPC's claimed gross. Surfaces a variance between what was claimed and what was
    actually received, and applies the same VAT / advance-tranche / retention / LC mechanism as the
    Invoice report to the GRN-verified gross instead."""
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    ipc = await session.get(Ipc, ipc_id)
    if not ipc or ipc.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="IPC not found")

    ipcs_result = await session.execute(select(Ipc).where(Ipc.contract_id == contract_id).order_by(Ipc.id))
    all_ipcs = ipcs_result.scalars().all()
    prior_ipcs = [i for i in all_ipcs if i.id < ipc.id]
    ipcs_upto = prior_ipcs + [ipc]
    prev_ipc_cutoff = prior_ipcs[-1].period_to if prior_ipcs else None

    claimed_gross_before = sum((i.gross for i in prior_ipcs), Decimal("0"))
    claimed_gross_upto = claimed_gross_before + ipc.gross

    lines_result = await session.execute(
        select(ContractLineItem).where(ContractLineItem.contract_id == contract_id).order_by(ContractLineItem.id)
    )
    line_items = lines_result.scalars().all()
    boq_total = sum((li.total for li in line_items), Decimal("0"))

    grn_result = await session.execute(select(GrnLine).where(GrnLine.contract_id == contract_id).order_by(GrnLine.received_date))
    all_grn = grn_result.scalars().all()
    grn_by_line: dict[int, list[GrnLine]] = {}
    for g in all_grn:
        grn_by_line.setdefault(g.line_item_id, []).append(g)

    # Build this contract's per-IPC GRN-verified gross series (mirrors ipc.gross, but receipt-verified),
    # so the same capped-recovery / cumulative-deduction machinery used for the claimed basis can be
    # replayed unchanged against it.
    grn_gross_series: list[Decimal] = []
    for idx, cur_ipc in enumerate(ipcs_upto):
        cutoff_prev = ipcs_upto[idx - 1].period_to if idx > 0 else None
        cutoff_cur = cur_ipc.period_to
        period_gross = Decimal("0")
        for li in line_items:
            entries = grn_by_line.get(li.id, [])
            period_gross += (_grn_cumulative(entries, cutoff_cur) - _grn_cumulative(entries, cutoff_prev)) * li.unit_rate
        grn_gross_series.append(period_gross)

    grn_gross_current = grn_gross_series[-1]
    grn_gross_before = sum(grn_gross_series[:-1], Decimal("0"))
    grn_gross_upto = grn_gross_before + grn_gross_current

    retention_series = [(g * contract.retention_pct / Decimal("100")).quantize(Decimal("0.01")) for g in grn_gross_series]
    retention_current, retention_before = retention_series[-1], sum(retention_series[:-1], Decimal("0"))
    retention_upto = retention_before + retention_current

    vat_series = [(g * contract.vat_pct / Decimal("100")).quantize(Decimal("0.01")) for g in grn_gross_series]
    vat_current, vat_before = vat_series[-1], sum(vat_series[:-1], Decimal("0"))
    vat_upto = vat_before + vat_current

    adv1_series = _capped_recovery_series(grn_gross_series, contract.advance_pct, contract.advance_amount)
    adv1_current, adv1_before = adv1_series[-1], sum(adv1_series[:-1], Decimal("0"))
    adv1_upto = adv1_before + adv1_current

    adv2_series = _capped_recovery_series(grn_gross_series, contract.advance2_pct, contract.advance2_amount)
    adv2_current, adv2_before = adv2_series[-1], sum(adv2_series[:-1], Decimal("0"))
    adv2_upto = adv2_before + adv2_current

    lc_series = _capped_recovery_series(grn_gross_series, contract.lc_pct, contract.lc_amount)
    lc_current, lc_before = lc_series[-1], sum(lc_series[:-1], Decimal("0"))
    lc_upto = lc_before + lc_current

    equipment_before = sum((i.equipment_rental_deduction for i in prior_ipcs), Decimal("0"))
    equipment_current = ipc.equipment_rental_deduction
    equipment_upto = equipment_before + equipment_current

    total_deduction_before = retention_before + adv1_before + adv2_before + lc_before + equipment_before
    total_deduction_current = retention_current + adv1_current + adv2_current + lc_current + equipment_current
    total_deduction_upto = total_deduction_before + total_deduction_current

    previous_net_paid = (grn_gross_before + vat_before) - total_deduction_before
    net_amount_current = (grn_gross_current + vat_current) - total_deduction_current

    variance_current = grn_gross_current - ipc.gross
    variance_flag = abs(variance_current) >= Decimal("100")

    line_rows: list[IpcGrnLineOut] = []
    for li in line_items:
        weight = (li.total / boq_total) if boq_total else Decimal("0")
        claimed_previous = (claimed_gross_before * weight).quantize(Decimal("0.01"))
        claimed_current = (ipc.gross * weight).quantize(Decimal("0.01"))
        claimed_to_date = claimed_previous + claimed_current

        entries = grn_by_line.get(li.id, [])
        grn_qty_to_date = _grn_cumulative(entries, ipc.period_to)
        grn_qty_previous = _grn_cumulative(entries, prev_ipc_cutoff)
        grn_qty_current = grn_qty_to_date - grn_qty_previous
        grn_amount_previous = grn_qty_previous * li.unit_rate
        grn_amount_current = grn_qty_current * li.unit_rate
        grn_amount_to_date = grn_qty_to_date * li.unit_rate

        line_variance = grn_amount_to_date - claimed_to_date
        line_rows.append(
            IpcGrnLineOut(
                code=li.code, description=li.description, uom=li.uom,
                contractQty=fmt_num(li.qty), unitRate=money(li.unit_rate),
                claimedQtyToDate=fmt_num(claimed_to_date / li.unit_rate if li.unit_rate else Decimal("0")),
                claimedAmountToDate=money(claimed_to_date),
                grnQtyPrevious=fmt_num(grn_qty_previous), grnAmountPrevious=money(grn_amount_previous),
                grnQtyCurrent=fmt_num(grn_qty_current), grnAmountCurrent=money(grn_amount_current),
                grnQtyToDate=fmt_num(grn_qty_to_date), grnAmountToDate=money(grn_amount_to_date),
                variance=money(line_variance), matched=abs(line_variance) < Decimal("100"),
            )
        )

    deductions = [
        IpcInvoiceDeductionRow(
            label=f"Retention ({contract.retention_pct}%)", rateLabel=f"{contract.retention_pct}%",
            previous=money(retention_before), current=money(retention_current), toDate=money(retention_upto),
        ),
        IpcInvoiceDeductionRow(
            label=f"Advance Recovery — Tranche 1 ({contract.advance_pct}%)", rateLabel=f"{contract.advance_pct}%",
            previous=money(adv1_before), current=money(adv1_current), toDate=money(adv1_upto),
        ),
        IpcInvoiceDeductionRow(
            label=f"Advance Recovery — Tranche 2 ({contract.advance2_pct}%)", rateLabel=f"{contract.advance2_pct}%",
            previous=money(adv2_before), current=money(adv2_current), toDate=money(adv2_upto),
        ),
        IpcInvoiceDeductionRow(
            label="Deduction for Equipment Rental", rateLabel="Fixed",
            previous=money(equipment_before), current=money(equipment_current), toDate=money(equipment_upto),
        ),
    ]

    def _pct_of_boq(amount: Decimal) -> str:
        if boq_total == 0:
            return "0%"
        return f"{round(float(amount / boq_total) * 100, 2)}%"

    totals = IpcGrnInvoiceTotals(
        claimedGrossToDate=money(claimed_gross_upto),
        claimedCompletionPct=f"{ipc.work_done_pct}%",
        grnGrossPrevious=money(grn_gross_before),
        grnGrossCurrent=money(grn_gross_current),
        grnGrossToDate=money(grn_gross_upto),
        grnCompletionPct=_pct_of_boq(grn_gross_upto),
        vatCurrentTotal=money(vat_current),
        vatToDateTotal=money(vat_upto),
        deductions=deductions,
        totalDeductionCurrent=money(total_deduction_current),
        totalDeductionToDate=money(total_deduction_upto),
        previousNetPaid=money(previous_net_paid),
        netAmountCurrent=money(net_amount_current),
        varianceCurrent=money(variance_current),
        varianceFlag=variance_flag,
    )

    def _pct_of_contract(amount: Decimal) -> str:
        if contract.contract_value == 0:
            return "0%"
        return f"{round(float(amount / contract.contract_value) * 100, 2)}%"

    advance_statements = [
        IpcInvoiceAdvanceStatement(
            label="Advance Tranche 1", pctOfContract=_pct_of_contract(contract.advance_amount),
            amount=money(contract.advance_amount), recoveredToDate=money(adv1_upto),
            outstanding=money(contract.advance_amount - adv1_upto), applicable=contract.advance_amount > 0,
        ),
        IpcInvoiceAdvanceStatement(
            label="Advance Tranche 2", pctOfContract=_pct_of_contract(contract.advance2_amount),
            amount=money(contract.advance2_amount), recoveredToDate=money(adv2_upto),
            outstanding=money(contract.advance2_amount - adv2_upto), applicable=contract.advance2_amount > 0,
        ),
    ]
    lc_statement = IpcInvoiceAdvanceStatement(
        label="Letter of Credit", pctOfContract=_pct_of_contract(contract.lc_amount),
        amount=money(contract.lc_amount), recoveredToDate=money(lc_upto),
        outstanding=money(contract.lc_amount - lc_upto), applicable=contract.lc_amount > 0,
    )
    retention_statement = IpcInvoiceRetentionStatement(
        pct=f"{contract.retention_pct}%", ofAmount=money(grn_gross_upto),
        heldToDate=money(retention_upto), released=money(Decimal("0")), netRetention=money(retention_upto),
    )

    return IpcGrnInvoiceResponse(
        contractId=contract.id, vendor=contract.vendor_name, project=contract.project_name, projectNo=contract.project_no,
        location=contract.location, contractNumber=contract.id, invoiceNumber=ipc.invoice_number or ipc.number,
        date=ipc.created_at.strftime("%d %b %Y"),
        periodFrom=ipc.period_from.strftime("%d-%b-%Y") if ipc.period_from else None,
        periodTo=ipc.period_to.strftime("%d-%b-%Y") if ipc.period_to else None,
        status=ipc.status, lines=line_rows, totals=totals,
        advanceStatements=advance_statements, lcStatement=lc_statement, retentionStatement=retention_statement,
    )


def _submission_confirmation_message(submission: VendorPortalSubmission, ipc: Ipc | None) -> str | None:
    if submission.status != "Certified" or not ipc:
        return None
    return f"Approved by PM — {ipc.number} created & pushed to Oracle (confirmation {ipc.oracle_confirmation_code})"


@router.get("/{contract_id}/vendor-submissions", response_model=list[VendorSubmissionOut])
async def list_vendor_submissions(contract_id: str, session: AsyncSession = Depends(get_session)) -> list[VendorSubmissionOut]:
    """Subcontractor progress claims from the Oracle vendor portal, awaiting PMO certification into an IPC."""
    result = await session.execute(
        select(VendorPortalSubmission).where(VendorPortalSubmission.contract_id == contract_id).order_by(VendorPortalSubmission.submitted_at)
    )
    submissions = result.scalars().all()
    ipc_ids = [s.ipc_id for s in submissions if s.ipc_id is not None]
    ipcs_by_id: dict[int, Ipc] = {}
    if ipc_ids:
        ipc_result = await session.execute(select(Ipc).where(Ipc.id.in_(ipc_ids)))
        ipcs_by_id = {i.id: i for i in ipc_result.scalars().all()}
    return [
        VendorSubmissionOut(
            id=s.id, period=s.period, workDonePct=f"{s.work_done_pct}%", grossClaimed=money(s.gross_claimed),
            submittedBy=s.submitted_by, submittedAt=s.submitted_at.strftime("%d %b %Y"), status=s.status,
            confirmationMessage=_submission_confirmation_message(s, ipcs_by_id.get(s.ipc_id) if s.ipc_id else None),
        )
        for s in submissions
    ]


@router.post("/{contract_id}/vendor-submissions/{submission_id}/certify", response_model=IpcRow, status_code=201)
async def certify_vendor_submission(contract_id: str, submission_id: int, session: AsyncSession = Depends(get_session)) -> IpcRow:
    """Certifies (PM-approves) a vendor portal work-progress claim into an actual IPC/GRN, and -
    same way Oracle PO creation is simulated on contract approval - simulates pushing it to
    Oracle for AP invoice creation in the same step, since real integration isn't wired up.
    """
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    submission = await session.get(VendorPortalSubmission, submission_id)
    if not submission or submission.contract_id != contract_id:
        raise HTTPException(status_code=404, detail="Vendor submission not found")
    if submission.status != "Submitted":
        raise HTTPException(status_code=400, detail=f"Submission is already '{submission.status}'")

    ipc = await _build_ipc(session, contract, submission.period, submission.work_done_pct, submission.gross_claimed)
    await session.flush()  # assigns ipc.id, needed for the confirmation code below
    ipc.oracle_push_status = "Pushed"
    ipc.oracle_confirmation_code = f"ORA-CONF-{100000 + ipc.id}"
    submission.status = "Certified"
    submission.ipc_id = ipc.id
    log_activity(
        session, entity_type="ipc", entity_id=ipc.number, action="certified", contract_id=contract_id,
        summary=(
            f"Invoice submission for {submission.period} approved by PM into {ipc.number} — {contract_id}, "
            f"{submission.work_done_pct}% complete, pushed to Oracle (confirmation {ipc.oracle_confirmation_code})"
        ),
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
        oraclePoDffRef=_po_dff_ref(contract),
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
