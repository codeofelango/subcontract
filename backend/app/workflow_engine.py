"""Shared engine that resolves and seeds ApprovalStep rows for a newly created
Contract/ChangeOrder/Penalty.

If an admin has configured and activated a WorkflowTemplate for the entity type, its steps are
used; otherwise falls back to the caller's hardcoded template so nothing breaks before any flow
has been built in the UI (see app/routers/workflows.py for how templates are authored).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApprovalStep, AppUser, WorkflowStepTemplate, WorkflowTemplate


async def resolve_chain(
    session: AsyncSession,
    applies_to: str,
    fallback_template: list[dict[str, str]],
) -> list[dict]:
    """Returns the ordered chain that's currently in effect for applies_to, as
    [{"role": str, "user": AppUser | None}, ...] - a user of None means "falls back to the
    raiser" (either because the step template has no assigned user, or the hardcoded fallback
    entry's name was blank). Used both to preview a chain before submission and to seed it.
    """
    active = await session.scalar(
        select(WorkflowTemplate).where(WorkflowTemplate.applies_to == applies_to, WorkflowTemplate.is_active == True)  # noqa: E712
    )

    if active:
        steps = (
            await session.execute(
                select(WorkflowStepTemplate).where(WorkflowStepTemplate.template_id == active.id).order_by(WorkflowStepTemplate.seq)
            )
        ).scalars().all()
        users_by_id = {u.id: u for u in (await session.execute(select(AppUser))).scalars().all()}
        return [{"role": s.role, "user": users_by_id.get(s.user_id) if s.user_id else None} for s in steps]

    return [{"role": t["role"], "user": None, "fallback_name": t["name"]} for t in fallback_template]


async def seed_approval_steps(
    session: AsyncSession,
    owner_type: str,
    owner_id: str,
    applies_to: str,
    fallback_template: list[dict[str, str]],
    raiser_name: str,
) -> None:
    rows = await resolve_chain(session, applies_to, fallback_template)

    for i, r in enumerate(rows):
        name = r["user"].name if r["user"] else (r.get("fallback_name") or raiser_name)
        state = "done" if i == 0 else ("current" if i == 1 else "pending")
        meta = "Completed" if state == "done" else ("Awaiting approval" if state == "current" else "Pending")
        session.add(ApprovalStep(
            owner_type=owner_type, owner_id=owner_id, seq=i, role=r["role"], approver_name=name,
            approver_user_id=r["user"].id if r["user"] else None, state=state, meta_note=meta,
        ))
