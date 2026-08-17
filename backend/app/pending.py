import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.business import money
from app.models import ApprovalStep, AppUser, ChangeOrder, Contract, Ipc, Penalty
from app.schemas.dashboard import PendingActionItem


def age_label(dt: datetime.datetime | datetime.date | None) -> str:
    if dt is None:
        return "—"
    today = datetime.date.today()
    d = dt.date() if isinstance(dt, datetime.datetime) else dt
    days = (today - d).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "1 day"
    return f"{days} days"


async def pending_actions(session: AsyncSession, current_user: AppUser | None = None) -> list[PendingActionItem]:
    """Items with an open approval decision. When current_user is an 'approver', this narrows to
    steps actually assigned to them (mirroring the identity check in
    app/approval_actions.py::_authorize) instead of showing every pending item in the org.
    Requester roles never act on approvals, so they get an empty list; admin/None sees everything.
    """
    contracts = (await session.execute(select(Contract))).scalars().all()
    penalties = (await session.execute(select(Penalty))).scalars().all()
    change_orders = (await session.execute(select(ChangeOrder))).scalars().all()
    ipcs = (await session.execute(select(Ipc))).scalars().all()
    contracts_by_id = {c.id: c for c in contracts}

    current_steps = (await session.execute(select(ApprovalStep).where(ApprovalStep.state == "current"))).scalars().all()
    step_by_owner = {(s.owner_type, s.owner_id): s for s in current_steps}

    def visible(owner_type: str, owner_id: str) -> bool:
        if current_user is None or current_user.role == "admin":
            return True
        if current_user.role != "approver":
            return False
        step = step_by_owner.get((owner_type, owner_id))
        if step is None:
            return True  # no configured chain - falls back to the plain admin/approver-only endpoints
        if step.approver_user_id is not None:
            return step.approver_user_id == current_user.id
        return step.approver_name == current_user.name

    pending: list[PendingActionItem] = []
    for c in contracts:
        if c.status == "Pending" and visible("contract", c.id):
            pending.append(PendingActionItem(
                ref=c.id, item="New contract approval", vendor=c.vendor_name, stage="Procurement Director",
                amount=money(c.contract_value), age=age_label(c.created_at), color="#b45309", bg="#fbf1e3",
            ))
    for p in penalties:
        if p.status == "In Approval" and visible("penalty", p.id):
            c = contracts_by_id.get(p.contract_id)
            pending.append(PendingActionItem(
                ref=p.id, item="Penalty approval", vendor=c.vendor_name if c else "—", stage="Awaiting approval",
                amount=money(p.amount), age=age_label(p.raised_on), color="#c0362c", bg="#fbeceb",
            ))
    if current_user is None or current_user.role == "admin":
        for i in ipcs:
            if i.status == "Certifying":
                c = contracts_by_id.get(i.contract_id)
                pending.append(PendingActionItem(
                    ref=f"{i.number.replace(' ', '-')}-{i.contract_id}", item="Progress payment",
                    vendor=c.vendor_name if c else "—", stage="Finance certify", amount=money(i.net_payable),
                    age=age_label(i.created_at), color="#3a5bd9", bg="#eef1fd",
                ))
    for co in change_orders:
        if co.status == "In Approval" and visible("change_order", co.id):
            c = contracts_by_id.get(co.contract_id)
            pending.append(PendingActionItem(
                ref=co.id, item="Change order approval", vendor=c.vendor_name if c else "—", stage="Procurement Director",
                amount="—", age=age_label(co.created_at), color="#12805c", bg="#e6f4ee",
            ))
    return pending
