"""Shared Approve/Reject/Revise state-machine logic for ApprovalStep chains - used by contracts,
change orders, and penalties alike, since they all seed from the same ApprovalStep table
(app/workflow_engine.py) and only differ in what happens once the chain finishes (PO creation, PO
revision, supplier debit, etc.), which stays in each router.
"""

import datetime
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApprovalStep, ApprovalStepHistory, AppUser
from app.schemas.change_orders import ApprovalStepOut

DECISIONS = ("approved", "rejected")


async def steps_to_out(session: AsyncSession, steps: list[ApprovalStep]) -> list[ApprovalStepOut]:
    acted_by_ids = {s.acted_by_id for s in steps if s.acted_by_id}
    names_by_id: dict[int, str] = {}
    if acted_by_ids:
        result = await session.execute(select(AppUser).where(AppUser.id.in_(acted_by_ids)))
        names_by_id = {u.id: u.name for u in result.scalars().all()}
    return [
        ApprovalStepOut(
            id=s.id, seq=s.seq, role=s.role, name=s.approver_name, meta=s.meta_note, state=s.state,
            decision=s.decision, actedBy=names_by_id.get(s.acted_by_id) if s.acted_by_id else None, actedAt=s.acted_at,
        )
        for s in steps
    ]


@dataclass
class DecisionResult:
    result: str  # "advanced" | "completed" | "rejected"
    step: ApprovalStep
    next_step: ApprovalStep | None


def _authorize(step: ApprovalStep, current_user: AppUser) -> None:
    if current_user.role == "admin":
        return
    if step.approver_user_id is not None and step.approver_user_id == current_user.id:
        return
    if step.approver_user_id is None and step.approver_name == current_user.name:
        return
    raise HTTPException(status_code=403, detail="It isn't your turn to act on this approval step")


def apply_decision(steps: list[ApprovalStep], current_user: AppUser, decision: str, comment: str | None) -> DecisionResult:
    if decision not in DECISIONS:
        raise HTTPException(status_code=422, detail=f"decision must be one of {DECISIONS}")

    current_idx = next((idx for idx, s in enumerate(steps) if s.state == "current"), None)
    if current_idx is None:
        raise HTTPException(status_code=400, detail="No current step to decide")
    step = steps[current_idx]
    _authorize(step, current_user)

    step.decision = decision
    step.acted_by_id = current_user.id
    step.acted_at = datetime.datetime.now(datetime.timezone.utc)
    if comment:
        step.meta_note = comment

    if decision == "rejected":
        step.state = "rejected"
        for later in steps[current_idx + 1 :]:
            later.state = "skipped"
            later.meta_note = "Skipped — chain rejected"
        return DecisionResult(result="rejected", step=step, next_step=None)

    step.state = "done"
    if not comment:
        step.meta_note = "Completed"
    if current_idx + 1 < len(steps):
        nxt = steps[current_idx + 1]
        nxt.state = "current"
        nxt.meta_note = "Awaiting approval"
        return DecisionResult(result="advanced", step=step, next_step=nxt)
    return DecisionResult(result="completed", step=step, next_step=None)


def apply_revision(
    steps: list[ApprovalStep], step: ApprovalStep, current_user: AppUser, new_decision: str, reason: str, session: AsyncSession
) -> DecisionResult:
    if new_decision not in DECISIONS:
        raise HTTPException(status_code=422, detail=f"decision must be one of {DECISIONS}")

    idx = steps.index(step)
    later = steps[idx + 1 :]
    if any(s.decision is not None for s in later):
        raise HTTPException(status_code=400, detail="The next step has already acted — this decision can no longer be revised")
    if not later and step.decision == "approved":
        raise HTTPException(
            status_code=400,
            detail="This was the final approval step and has already taken effect (PO/PO revision/supplier debit) — it can no longer be revised",
        )
    if current_user.id != step.acted_by_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the approver who acted (or an Admin) can revise this decision")
    if new_decision == step.decision:
        raise HTTPException(status_code=400, detail="That is already the current decision")

    previous_decision, previous_state = step.decision, step.state
    for s in later:
        s.decision, s.state, s.acted_by_id, s.acted_at, s.meta_note = None, "pending", None, None, "Pending"
    step.decision, step.acted_by_id, step.acted_at = None, None, None
    step.state, step.meta_note = "current", "Awaiting approval"

    result = apply_decision(steps, current_user, new_decision, reason)

    session.add(ApprovalStepHistory(
        step_id=step.id, previous_decision=previous_decision, previous_state=previous_state,
        new_decision=new_decision, new_state=result.step.state, changed_by_id=current_user.id, reason=reason,
    ))
    return result
