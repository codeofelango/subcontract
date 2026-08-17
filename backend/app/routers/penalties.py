import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.approval_actions import apply_decision, apply_revision, steps_to_out
from app.auth import assert_contract_visible, get_current_user, require_roles
from app.business import money
from app.database import get_session
from app.email_service import attachments_for_email, send_workflow_notification
from app.models import ApprovalStep, AppUser, Contract, Penalty
from app.schemas.attachments import AttachmentOut
from app.schemas.change_orders import DecisionRequest, ReviseDecisionRequest
from app.schemas.penalties import NewPenaltyRequest, PenaltyDetailResponse, PenaltyField, SlaBreach
from app.storage import claim_attachments, get_owner_attachments, require_attachment
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
async def get_penalty(
    penalty_id: str, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> PenaltyDetailResponse:
    penalty = await session.get(Penalty, penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")
    contract = await session.get(Contract, penalty.contract_id)
    assert_contract_visible(current_user, contract)

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
    approval_steps = await steps_to_out(session, steps)
    attachments = await get_owner_attachments(session, "penalty", penalty_id)

    return PenaltyDetailResponse(
        id=penalty.id, title=f"Penalty — {contract.vendor_name}", status=penalty.status,
        fields=fields, attachment=penalty.attachment_ref,
        attachments=[
            AttachmentOut(id=a.id, filename=a.filename, contentType=a.content_type, sizeBytes=a.size_bytes, uploadedAt=a.uploaded_at.strftime("%d %b %Y %H:%M"))
            for a in attachments
        ],
        slaBreach=sla_breach, approvalSteps=approval_steps,
    )


async def _notify_current_step(session: AsyncSession, penalty: Penalty, steps: list[ApprovalStep]) -> None:
    current = next((s for s in steps if s.state == "current"), None)
    if not current or not current.approver_user_id:
        return
    approver = await session.get(AppUser, current.approver_user_id)
    if not approver:
        return
    attachments = await get_owner_attachments(session, "penalty", penalty.id)
    await send_workflow_notification(
        to_email=approver.email, to_name=approver.name, heading=f"Awaiting your approval — {penalty.id}",
        owner_type="penalty", owner_id=penalty.id,
        rows=[("Reason", penalty.reason), ("Amount", money(penalty.amount)), ("Your role", current.role)],
        link_path=f"/penalties/{penalty.id}", attachments=attachments_for_email(attachments),
    )


async def _notify_raiser(session: AsyncSession, penalty: Penalty, heading: str, extra_rows: list[tuple[str, str]]) -> None:
    raiser = (await session.execute(select(AppUser).where(AppUser.name == penalty.raised_by))).scalars().first()
    if not raiser:
        return
    attachments = await get_owner_attachments(session, "penalty", penalty.id)
    await send_workflow_notification(
        to_email=raiser.email, to_name=raiser.name, heading=heading, owner_type="penalty", owner_id=penalty.id,
        rows=[("Reason", penalty.reason), ("Amount", money(penalty.amount)), *extra_rows],
        link_path=f"/penalties/{penalty.id}", attachments=attachments_for_email(attachments),
    )


@router.post("", status_code=201, dependencies=[Depends(require_roles("admin", "procurement_requester", "hr_requester"))])
async def create_penalty(
    payload: NewPenaltyRequest, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> dict:
    await require_attachment(session, payload.draftToken)

    contract = await session.get(Contract, payload.contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    assert_contract_visible(current_user, contract)

    result = await session.execute(select(Penalty))
    count = len(result.scalars().all())
    year = datetime.date.today().year
    penalty_id = f"PN-{year}-{count + 1:03d}"

    penalty = Penalty(
        id=penalty_id, contract_id=payload.contractId, reason=payload.reason, basis=payload.basis,
        amount=Decimal(str(payload.amount)), status="In Approval", attachment_ref="",
        raised_by=payload.raisedBy, raised_on=datetime.date.today(),
        sla_actual_pct=Decimal(str(payload.slaActualPct)), sla_target_pct=Decimal(str(payload.slaTargetPct)),
        sla_breach_months=payload.slaBreachMonths, sla_label=payload.slaLabel,
    )
    session.add(penalty)
    await seed_approval_steps(
        session, owner_type="penalty", owner_id=penalty_id, applies_to="penalty",
        fallback_template=PENALTY_STEP_TEMPLATE, raiser_name=payload.raisedBy,
    )
    await claim_attachments(session, payload.draftToken, "penalty", penalty_id)
    attachments = await get_owner_attachments(session, "penalty", penalty_id)
    penalty.attachment_ref = ", ".join(a.filename for a in attachments)

    log_activity(
        session, entity_type="penalty", entity_id=penalty_id, action="raised", contract_id=payload.contractId,
        summary=f"Penalty {penalty_id} raised against {contract.vendor_name} ({payload.contractId}) — {payload.reason}, amount {money(Decimal(str(payload.amount)))}",
    )
    await session.commit()
    await _notify_current_step(session, penalty, await _steps_for(session, penalty_id))
    return {"id": penalty_id, "status": "In Approval"}


@router.post("/{penalty_id}/decide")
async def decide_step(
    penalty_id: str, payload: DecisionRequest, session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> dict:
    penalty = await session.get(Penalty, penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")

    steps = await _steps_for(session, penalty_id)
    result = apply_decision(steps, current_user, payload.decision, payload.comment)

    if result.result == "rejected":
        penalty.status = "Rejected"
        summary = f"Penalty {penalty_id} rejected at step '{result.step.role}' by {current_user.name}"
        await _notify_raiser(session, penalty, f"Penalty {penalty.id} was rejected", [("Rejected by", current_user.name), ("Comment", payload.comment or "—")])
    elif result.result == "completed":
        penalty.status = "Debited"
        summary = f"Penalty {penalty_id} fully approved — supplier account debited {money(penalty.amount)}"
        await _notify_raiser(session, penalty, f"Penalty {penalty.id} was approved and debited", [("Debited", money(penalty.amount))])
    else:
        summary = f"Penalty {penalty_id} — step '{result.step.role}' {payload.decision} by {current_user.name}, now awaiting '{result.next_step.role}'"
        await _notify_current_step(session, penalty, steps)

    log_activity(session, entity_type="penalty", entity_id=penalty_id, action="step_decided", contract_id=penalty.contract_id, summary=summary)
    await session.commit()
    return {"id": penalty_id, "status": penalty.status}


@router.post("/{penalty_id}/steps/{step_id}/revise")
async def revise_step(
    penalty_id: str, step_id: int, payload: ReviseDecisionRequest, session: AsyncSession = Depends(get_session),
    current_user: AppUser = Depends(get_current_user),
) -> dict:
    penalty = await session.get(Penalty, penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")

    steps = await _steps_for(session, penalty_id)
    step = next((s for s in steps if s.id == step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail="Approval step not found")

    result = apply_revision(steps, step, current_user, payload.decision, payload.reason, session)

    if result.result == "rejected":
        penalty.status = "Rejected"
        summary = f"Penalty {penalty_id} — step '{result.step.role}' revised to rejected by {current_user.name} ({payload.reason})"
    elif result.result == "completed":
        penalty.status = "Debited"
        summary = f"Penalty {penalty_id} — step '{result.step.role}' revised to approved by {current_user.name} ({payload.reason}) — supplier account debited {money(penalty.amount)}"
    else:
        penalty.status = "In Approval"
        summary = f"Penalty {penalty_id} — step '{result.step.role}' revised to {payload.decision} by {current_user.name} ({payload.reason})"
        await _notify_current_step(session, penalty, steps)

    await _notify_raiser(session, penalty, f"A decision on penalty {penalty.id} was revised", [("Revised by", current_user.name), ("New decision", payload.decision), ("Reason", payload.reason)])
    log_activity(session, entity_type="penalty", entity_id=penalty_id, action="step_revised", contract_id=penalty.contract_id, summary=summary)
    await session.commit()
    return {"id": penalty_id, "status": penalty.status}
