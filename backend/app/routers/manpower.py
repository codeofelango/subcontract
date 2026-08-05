from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import log_activity
from app.business import fmt_num, manpower_variance, money
from app.database import get_session
from app.models import Contract, TimesheetLine, VendorInvoiceLine
from app.schemas.manpower import ManpowerContext, ManpowerResponse, ManpowerRow, ManpowerTotal

router = APIRouter(prefix="/manpower", tags=["manpower"])


async def _load(contract_id: str, period: str, session: AsyncSession):
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    ts = (await session.execute(
        select(TimesheetLine).where(TimesheetLine.contract_id == contract_id, TimesheetLine.period == period)
    )).scalars().all()
    inv = (await session.execute(
        select(VendorInvoiceLine).where(VendorInvoiceLine.contract_id == contract_id, VendorInvoiceLine.period == period)
    )).scalars().all()
    inv_by_title = {v.job_title: v.invoiced_amount for v in inv}
    return contract, ts, inv_by_title


@router.get("/{contract_id}", response_model=ManpowerResponse)
async def get_manpower(contract_id: str, period: str, session: AsyncSession = Depends(get_session)) -> ManpowerResponse:
    contract, ts, inv_by_title = await _load(contract_id, period, session)

    rows: list[ManpowerRow] = []
    total_contract = Decimal("0")
    total_invoiced = Decimal("0")
    matched_total = Decimal("0")
    worst_row = None
    worst_abs = Decimal("-1")

    for line in ts:
        invoiced = inv_by_title.get(line.job_title, Decimal("0"))
        contract_amount, variance, matched = manpower_variance(line.reg_hours, line.reg_rate, line.ot_hours, line.ot_rate, invoiced)
        total_contract += contract_amount
        total_invoiced += invoiced
        if matched:
            matched_total += contract_amount
        if abs(variance) > worst_abs:
            worst_abs = abs(variance)
            worst_row = (line.job_title, variance)

        sign = "+" if variance > 0 else ("−" if variance < 0 else "")
        rows.append(ManpowerRow(
            title=line.job_title, reg=fmt_num(line.reg_hours), regRate=f"{line.reg_rate:.0f}",
            ot=fmt_num(line.ot_hours), otRate=f"{line.ot_rate:.1f}", contract=fmt_num(contract_amount),
            invoiced=fmt_num(invoiced), variance=f"{sign}{fmt_num(abs(variance))}",
            varColor="#667085" if matched else "#c0362c",
            status="Matched" if matched else "Review", color="#12805c" if matched else "#b45309",
            bg="#e6f4ee" if matched else "#fbf1e3",
        ))

    net_variance = total_invoiced - total_contract
    note = None
    if worst_row and worst_abs >= Decimal("100"):
        title, variance = worst_row
        direction = "overbilled" if variance > 0 else "underbilled"
        note = (
            f"{title} — invoiced amount {'exceeds' if variance > 0 else 'is below'} the contract-computed amount "
            f"by {money(abs(variance))} ({direction} at contract rate). Adjust invoice or attach approved authorisation."
        )

    return ManpowerResponse(
        context=ManpowerContext(
            contractId=contract.id, vendor=contract.vendor_name, period=period,
            netVariance=f"{'+ ' if net_variance > 0 else ('− ' if net_variance < 0 else '')}{money(abs(net_variance))}",
            netVarianceColor="#c0362c" if net_variance != 0 else "#12805c",
        ),
        rows=rows,
        total=ManpowerTotal(contract=money(total_contract), invoiced=money(total_invoiced), variance=f"{'+ ' if net_variance >= 0 else '− '}{money(abs(net_variance))}"),
        varianceNote=note,
        matchedTotal=money(matched_total),
    )


@router.post("/{contract_id}/approve-matched")
async def approve_matched(contract_id: str, period: str, session: AsyncSession = Depends(get_session)) -> dict:
    contract, ts, inv_by_title = await _load(contract_id, period, session)
    matched_total = Decimal("0")
    for line in ts:
        invoiced = inv_by_title.get(line.job_title, Decimal("0"))
        contract_amount, _, matched = manpower_variance(line.reg_hours, line.reg_rate, line.ot_hours, line.ot_rate, invoiced)
        if matched:
            matched_total += contract_amount
    log_activity(
        session, entity_type="manpower", entity_id=f"{contract_id}:{period}", action="approved_matched", contract_id=contract_id,
        summary=f"Manpower reconciliation for {contract.vendor_name} — {period}: matched lines approved for payment of {money(matched_total)}",
    )
    await session.commit()
    return {"status": "approved", "amountPaid": money(matched_total)}


@router.post("/{contract_id}/dispute")
async def raise_dispute(contract_id: str, period: str, session: AsyncSession = Depends(get_session)) -> dict:
    contract, _, _ = await _load(contract_id, period, session)
    log_activity(
        session, entity_type="manpower", entity_id=f"{contract_id}:{period}", action="dispute_raised", contract_id=contract_id,
        summary=f"Manpower dispute raised for {contract.vendor_name} — {period}: invoiced amount vs contract-computed amount under review",
    )
    await session.commit()
    return {"status": "dispute_raised", "contractId": contract_id, "period": period}
