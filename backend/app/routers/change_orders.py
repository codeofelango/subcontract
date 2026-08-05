import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.business import co_value_impact, fmt_num, money
from app.database import get_session
from app.models import ApprovalStep, ChangeOrder, ChangeOrderLine, Contract, ContractLineItem
from app.schemas.change_orders import (
    ApprovalStepOut,
    ChangeOrderDetailResponse,
    CoContext,
    CoHistoryRow,
    CoLineRow,
    CoValueRow,
    NewChangeOrderRequest,
)
from app.workflow_engine import seed_approval_steps

router = APIRouter(prefix="/change-orders", tags=["change-orders"])

CO_STEP_TEMPLATE = [
    {"role": "Raised by Project Manager", "name": "R. Menon"},
    {"role": "QS / Cost Verification", "name": "K. Ibrahim"},
    {"role": "Procurement Director", "name": "S. Farooq"},
    {"role": "Revise PO in Oracle", "name": ""},
]


async def _steps_for(session: AsyncSession, co_id: str) -> list[ApprovalStep]:
    result = await session.execute(
        select(ApprovalStep).where(ApprovalStep.owner_type == "change_order", ApprovalStep.owner_id == co_id).order_by(ApprovalStep.seq)
    )
    return list(result.scalars().all())


@router.get("/{contract_id}", response_model=ChangeOrderDetailResponse)
async def get_change_orders(contract_id: str, session: AsyncSession = Depends(get_session)) -> ChangeOrderDetailResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    result = await session.execute(select(ChangeOrder).where(ChangeOrder.contract_id == contract_id).order_by(ChangeOrder.created_at))
    cos = list(result.scalars().all())
    if not cos:
        raise HTTPException(status_code=404, detail="No change orders for this contract")
    active = next((c for c in cos if c.status == "In Approval"), cos[-1])

    lines_result = await session.execute(select(ChangeOrderLine).where(ChangeOrderLine.change_order_id == active.id))
    lines = list(lines_result.scalars().all())

    net_impact = Decimal("0")
    line_rows = []
    for line in lines:
        impact = co_value_impact(line.original_qty, line.revised_qty, line.contract_rate)
        net_impact += impact
        delta = line.revised_qty - line.original_qty
        line_rows.append(CoLineRow(
            code=line.code, desc=line.description, orig=fmt_num(line.original_qty), rev=fmt_num(line.revised_qty),
            delta=f"{'+' if delta > 0 else ''}{fmt_num(delta)}", deltaColor="#12805c" if delta > 0 else "#c0362c",
            rate=fmt_num(line.contract_rate), impact=f"{'+ ' if impact > 0 else '− '}{money(abs(impact))}",
            impactColor="#12805c" if impact > 0 else "#c0362c",
        ))

    revised_value = contract.contract_value + net_impact
    value_rows = [
        CoValueRow(k="Original contract value", v=money(contract.contract_value), w=500, c="#475467"),
        CoValueRow(k="Net change impact", v=f"{'+ ' if net_impact > 0 else '− '}{money(abs(net_impact))}", w=600, c="#12805c" if net_impact > 0 else "#c0362c"),
        CoValueRow(k="Revised contract value", v=money(revised_value), w=700, c="#101828"),
        CoValueRow(k="Retention (revised)", v=money(revised_value * contract.retention_pct / Decimal("100")), w=500, c="#b45309"),
        CoValueRow(k="Advance — unchanged", v=money(contract.advance_amount), w=500, c="#2c7fb0"),
    ]

    steps = await _steps_for(session, active.id)
    approval_steps = [ApprovalStepOut(seq=s.seq, role=s.role, name=s.approver_name, meta=s.meta_note, state=s.state) for s in steps]

    history = []
    for co in cos:
        co_lines = (await session.execute(select(ChangeOrderLine).where(ChangeOrderLine.change_order_id == co.id))).scalars().all()
        impact = sum((co_value_impact(l.original_qty, l.revised_qty, l.contract_rate) for l in co_lines), Decimal("0"))
        sc, sbg = status_colors_co(co.status)
        history.append(CoHistoryRow(
            id=co.id, reason=co.reason, impact=f"{'+ ' if impact > 0 else '− '}{money(abs(impact))}",
            impactColor="#12805c" if impact > 0 else "#c0362c", po=co.po_revision_label, status=co.status, color=sc, bg=sbg,
        ))

    return ChangeOrderDetailResponse(
        context=CoContext(id=active.id, title=active.title, contractId=contract.id, vendor=contract.vendor_name, po=contract.oracle_po or "—", status=active.status),
        affectedLineItems=line_rows,
        history=history,
        valueRows=value_rows,
        approvalSteps=approval_steps,
    )


def status_colors_co(status: str) -> tuple[str, str]:
    return {"Approved": ("#12805c", "#e6f4ee"), "In Approval": ("#b45309", "#fbf1e3"), "Draft": ("#667085", "#f0f1f4")}.get(status, ("#667085", "#f0f1f4"))


@router.post("", status_code=201)
async def create_change_order(payload: NewChangeOrderRequest, session: AsyncSession = Depends(get_session)) -> dict:
    contract = await session.get(Contract, payload.contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    result = await session.execute(select(ChangeOrder).where(ChangeOrder.contract_id == payload.contractId))
    count = len(result.scalars().all())
    year = datetime.date.today().year
    co_id = f"CO-{year}-{count + 1:03d}"

    co = ChangeOrder(id=co_id, contract_id=payload.contractId, title=payload.title, reason=payload.reason, status="In Approval", po_revision_label="Rev pending")
    session.add(co)
    for line in payload.lines:
        session.add(ChangeOrderLine(
            change_order_id=co_id, code=line.code, description=line.description,
            original_qty=Decimal(str(line.originalQty)), revised_qty=Decimal(str(line.revisedQty)),
            contract_rate=Decimal(str(line.contractRate)),
        ))
    await seed_approval_steps(
        session, owner_type="change_order", owner_id=co_id, applies_to="change_order",
        fallback_template=CO_STEP_TEMPLATE, raiser_name="",
    )

    log_activity(
        session, entity_type="change_order", entity_id=co_id, action="created", contract_id=payload.contractId,
        summary=f"Change order {co_id} raised for {contract.vendor_name} ({payload.contractId}) — {payload.reason}",
    )
    await session.commit()
    return {"id": co_id, "status": "In Approval"}


@router.post("/{co_id}/advance-step")
async def advance_step(co_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    co = await session.get(ChangeOrder, co_id)
    if not co:
        raise HTTPException(status_code=404, detail="Change order not found")

    steps = await _steps_for(session, co_id)
    current_idx = next((idx for idx, s in enumerate(steps) if s.state == "current"), None)
    if current_idx is None:
        raise HTTPException(status_code=400, detail="No current step to advance")

    steps[current_idx].state = "done"
    steps[current_idx].meta_note = "Completed"
    completed_role = steps[current_idx].role
    if current_idx + 1 < len(steps):
        steps[current_idx + 1].state = "current"
        steps[current_idx + 1].meta_note = "Awaiting approval"
        summary = f"Change order {co_id} — step '{completed_role}' completed, now awaiting '{steps[current_idx + 1].role}'"
    else:
        co.status = "Approved"
        contract = await session.get(Contract, co.contract_id)
        applied = 0
        if contract:
            if contract.oracle_po_rev:
                rev_num = int(contract.oracle_po_rev.split(" ")[-1]) + 1
                contract.oracle_po_rev = f"Rev {rev_num}"
                co.po_revision_label = contract.oracle_po_rev

            co_lines = (await session.execute(select(ChangeOrderLine).where(ChangeOrderLine.change_order_id == co_id))).scalars().all()
            contract_lines = (
                await session.execute(select(ContractLineItem).where(ContractLineItem.contract_id == co.contract_id))
            ).scalars().all()
            lines_by_code = {cl.code: cl for cl in contract_lines}

            net_impact = Decimal("0")
            for co_line in co_lines:
                net_impact += co_value_impact(co_line.original_qty, co_line.revised_qty, co_line.contract_rate)
                matching = lines_by_code.get(co_line.code)
                if matching:
                    matching.previous_qty = matching.qty
                    matching.qty = co_line.revised_qty
                    matching.total = matching.qty * matching.unit_rate
                    matching.revised_by_co = co_id
                    applied += 1
            contract.contract_value = contract.contract_value + net_impact

        summary = f"Change order {co_id} approved — PO revised to {co.po_revision_label}, {applied} line item(s) revised on contract"

    log_activity(session, entity_type="change_order", entity_id=co_id, action="step_advanced", contract_id=co.contract_id, summary=summary)
    await session.commit()
    return {"id": co_id, "status": co.status}
