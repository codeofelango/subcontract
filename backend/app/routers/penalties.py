import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.business import money
from app.database import get_session
from app.models import ApprovalStep, Contract, Penalty
from app.schemas.change_orders import ApprovalStepOut
from app.schemas.penalties import NewPenaltyRequest, PenaltyDetailResponse, PenaltyField, SlaBreach
from app.workflow_engine import seed_approval_steps

router = APIRouter(prefix="/penalties", tags=["penalties"])

PENALTY_STEP_TEMPLATE = [
    {"role": "Raised by Project Manager", "name": ""},
    {"role": "PM Acknowledge", "name": ""},
    {"role": "COO Approval", "name": "A. Khalil"},
    {"role": "Procurement Director", "name": "S. Farooq"},
    {"role": "CFO Approval", "name": "M. Haddad"},
    {"role": "Debit Supplier Account", "name": "Finance / AP"},
]


async def _steps_for(session: AsyncSession, penalty_id: str) -> list[ApprovalStep]:
    result = await session.execute(
        select(ApprovalStep).where(ApprovalStep.owner_type == "penalty", ApprovalStep.owner_id == penalty_id).order_by(ApprovalStep.seq)
    )
    return list(result.scalars().all())


@router.get("/{penalty_id}", response_model=PenaltyDetailResponse)
async def get_penalty(penalty_id: str, session: AsyncSession = Depends(get_session)) -> PenaltyDetailResponse:
    penalty = await session.get(Penalty, penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")
    contract = await session.get(Contract, penalty.contract_id)

    fields = [
        PenaltyField(label="Contract Number", value=penalty.contract_id, weight=600, color="var(--accent,#3a5bd9)"),
        PenaltyField(label="Project", value=contract.project_name, weight=500, color="#101828"),
        PenaltyField(label="Reason", value=penalty.reason, weight=500, color="#101828"),
        PenaltyField(label="Basis", value=penalty.basis, weight=500, color="#101828"),
        PenaltyField(label="Penalty Amount", value=money(penalty.amount), weight=700, color="#c0362c"),
        PenaltyField(label="Raised On", value=f"{penalty.raised_on.strftime('%d %b %Y')} by {penalty.raised_by}", weight=500, color="#101828"),
    ]
    sla_breach = SlaBreach(
        actualPct=f"{penalty.sla_actual_pct:.0f}%",
        label=penalty.sla_label,
        detail=f"vs SLA target ≥ {penalty.sla_target_pct:.0f}% — breached for {penalty.sla_breach_months} consecutive month(s). Penalty computed per {penalty.basis}.",
    )
    steps = await _steps_for(session, penalty_id)
    approval_steps = [ApprovalStepOut(seq=s.seq, role=s.role, name=s.approver_name, meta=s.meta_note, state=s.state) for s in steps]

    return PenaltyDetailResponse(
        id=penalty.id, title=f"Penalty — {contract.vendor_name}", status=penalty.status,
        fields=fields, attachment=penalty.attachment_ref, slaBreach=sla_breach, approvalSteps=approval_steps,
    )


@router.post("", status_code=201)
async def create_penalty(payload: NewPenaltyRequest, session: AsyncSession = Depends(get_session)) -> dict:
    if not payload.attachmentRef.strip():
        raise HTTPException(status_code=400, detail="A supporting attachment is mandatory to raise a penalty")

    contract = await session.get(Contract, payload.contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    result = await session.execute(select(Penalty))
    count = len(result.scalars().all())
    year = datetime.date.today().year
    penalty_id = f"PN-{year}-{count + 1:03d}"

    penalty = Penalty(
        id=penalty_id, contract_id=payload.contractId, reason=payload.reason, basis=payload.basis,
        amount=Decimal(str(payload.amount)), status="In Approval", attachment_ref=payload.attachmentRef,
        raised_by=payload.raisedBy, raised_on=datetime.date.today(),
        sla_actual_pct=Decimal(str(payload.slaActualPct)), sla_target_pct=Decimal(str(payload.slaTargetPct)),
        sla_breach_months=payload.slaBreachMonths, sla_label=payload.slaLabel,
    )
    session.add(penalty)
    await seed_approval_steps(
        session, owner_type="penalty", owner_id=penalty_id, applies_to="penalty",
        fallback_template=PENALTY_STEP_TEMPLATE, raiser_name=payload.raisedBy,
    )

    log_activity(
        session, entity_type="penalty", entity_id=penalty_id, action="raised", contract_id=payload.contractId,
        summary=f"Penalty {penalty_id} raised against {contract.vendor_name} ({payload.contractId}) — {payload.reason}, amount {money(Decimal(str(payload.amount)))}",
    )
    await session.commit()
    return {"id": penalty_id, "status": "In Approval"}


@router.post("/{penalty_id}/advance-step")
async def advance_step(penalty_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    penalty = await session.get(Penalty, penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")

    steps = await _steps_for(session, penalty_id)
    current_idx = next((idx for idx, s in enumerate(steps) if s.state == "current"), None)
    if current_idx is None:
        raise HTTPException(status_code=400, detail="No current step to advance")

    steps[current_idx].state = "done"
    steps[current_idx].meta_note = "Completed"
    completed_role = steps[current_idx].role
    if current_idx + 1 < len(steps):
        steps[current_idx + 1].state = "current"
        steps[current_idx + 1].meta_note = "Awaiting approval"
        summary = f"Penalty {penalty_id} — step '{completed_role}' completed, now awaiting '{steps[current_idx + 1].role}'"
    else:
        penalty.status = "Debited"
        summary = f"Penalty {penalty_id} fully approved — supplier account debited {money(penalty.amount)}"

    log_activity(session, entity_type="penalty", entity_id=penalty_id, action="step_advanced", contract_id=penalty.contract_id, summary=summary)

    await session.commit()
    return {"id": penalty_id, "status": penalty.status}
