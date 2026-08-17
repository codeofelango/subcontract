import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.business import money, progress_color, rating_for, score_kpi
from app.database import get_session
from app.models import AppUser, Contract, Evaluation, EvaluationKpiRow, Ipc, Penalty
from app.pending import pending_actions
from app.schemas.dashboard import AlertItem, DashboardResponse, KpiItem, ServiceMixItem, VendorSummaryItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SERVICE_MIX_LABELS = {
    "Hard FM (MEP)": ("Hard FM (MEP)", "#3a5bd9"),
    "Manpower": ("Manpower Supply", "#4b9fd1"),
    "Construction / JR": ("Construction / JR", "#7a5bd9"),
    "Soft Services": ("Soft Services", "#12a679"),
}


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> DashboardResponse:
    contracts = (await session.execute(select(Contract))).scalars().all()
    ipcs = (await session.execute(select(Ipc))).scalars().all()
    penalties = (await session.execute(select(Penalty))).scalars().all()

    active_contracts = [c for c in contracts if c.status == "Active"]
    portfolio_value = sum((c.contract_value for c in contracts), Decimal("0"))
    executed_spend = sum((i.net_payable for i in ipcs), Decimal("0"))
    retention_held = sum((i.retention for i in ipcs), Decimal("0"))
    retention_releasable = sum(
        (i.retention for i in ipcs if i.status == "Paid" and i.work_done_pct >= Decimal("95")), Decimal("0")
    )
    advance_outstanding = sum(
        (c.advance_amount - sum((i.advance_recovered for i in ipcs if i.contract_id == c.id), Decimal("0")) for c in contracts),
        Decimal("0"),
    )
    today = datetime.date.today()
    expiring_soon = [c for c in contracts if c.expiry_date and 0 <= (c.expiry_date - today).days <= 30]

    committed_pct = round(float(executed_spend / portfolio_value) * 100) if portfolio_value else 0

    kpis = [
        KpiItem(label="Active Contracts", value=str(len(active_contracts)), delta=f"{len(contracts)} total in portfolio", deltaColor="#12805c"),
        KpiItem(label="Portfolio Value", value=money(portfolio_value), delta=f"across {len({c.project_name for c in contracts})} projects", deltaColor="#667085"),
        KpiItem(label="Executed Spend", value=money(executed_spend), delta=f"{committed_pct}% committed", deltaColor="#667085"),
        KpiItem(label="Retention Held", value=money(retention_held), delta=f"{money(retention_releasable)} releasable", deltaColor="#b45309"),
        KpiItem(label="Advance Outstanding", value=money(advance_outstanding), delta="to recover", deltaColor="#b45309"),
        KpiItem(label="Expiring ≤30d", value=str(len(expiring_soon)), delta="renew or close", deltaColor="#c0362c"),
    ]

    alerts: list[AlertItem] = []
    for c in sorted(expiring_soon, key=lambda c: c.expiry_date):
        days = (c.expiry_date - today).days
        alerts.append(AlertItem(
            title=f"{c.vendor_name} — contract expiring in {days} days",
            detail=f"{c.id} · {c.project_name} · {c.progress_pct}% complete",
            tag="Expiring", color="#b45309", bg="#fbf1e3",
        ))
    for p in penalties:
        if p.sla_actual_pct < p.sla_target_pct:
            alerts.append(AlertItem(
                title=f"{(await session.get(Contract, p.contract_id)).vendor_name} — SLA breach ({p.sla_label})",
                detail=f"Below {p.sla_target_pct}% for {p.sla_breach_months} consecutive month(s) → penalty eligible",
                tag="SLA", color="#c0362c", bg="#fbeceb",
            ))
    for c in contracts:
        if 0 < c.progress_pct < 40 and c.status == "Active":
            alerts.append(AlertItem(
                title=f"{c.vendor_name} — progress tracking low ({c.progress_pct}%)",
                detail=f"{c.id} · {c.project_name} · look-ahead slipping",
                tag="Progress", color="#c0362c", bg="#fbeceb",
            ))
    for i in ipcs:
        if i.status == "Certifying":
            c = await session.get(Contract, i.contract_id)
            alerts.append(AlertItem(
                title=f"{c.vendor_name} — {i.number} awaiting certification",
                detail=f"{money(i.net_payable)} net payable pending Finance",
                tag="Payment", color="#3a5bd9", bg="#eef1fd",
            ))

    service_mix_totals: dict[str, Decimal] = {}
    for c in contracts:
        service_mix_totals[c.service_type] = service_mix_totals.get(c.service_type, Decimal("0")) + c.contract_value
    service_mix = []
    for key, (label, color) in SERVICE_MIX_LABELS.items():
        amount = service_mix_totals.get(key, Decimal("0"))
        pct = round(float(amount / portfolio_value) * 100) if portfolio_value else 0
        service_mix.append(ServiceMixItem(label=label, amount=money(amount), pct=f"{pct}%", width=f"{pct}%", color=color))

    pending = await pending_actions(session, current_user)

    # Vendor overview - groups contracts by vendor, pulling in each vendor's latest evaluation score if one exists.
    evaluations = (await session.execute(select(Evaluation).order_by(Evaluation.id.desc()))).scalars().all()
    latest_eval_by_vendor: dict[str, Evaluation] = {}
    for e in evaluations:
        latest_eval_by_vendor.setdefault(e.subcontractor, e)  # already ordered newest-first, so first hit wins

    kpi_rows_all = (await session.execute(select(EvaluationKpiRow))).scalars().all()
    kpi_by_eval: dict[int, list[EvaluationKpiRow]] = {}
    for k in kpi_rows_all:
        kpi_by_eval.setdefault(k.evaluation_id, []).append(k)

    def _eval_score(evaluation_id: int) -> float:
        total = 0.0
        for k in kpi_by_eval.get(evaluation_id, []):
            total += float(k.weight) * score_kpi(float(k.actual), float(k.target_value), k.direction) / 100
        return round(total * 10) / 10

    vendor_groups: dict[str, list[Contract]] = {}
    for c in contracts:
        vendor_groups.setdefault(c.vendor_name, []).append(c)

    vendors: list[VendorSummaryItem] = []
    for vendor_name, vc in sorted(vendor_groups.items(), key=lambda kv: sum((x.contract_value for x in kv[1]), Decimal("0")), reverse=True):
        total_value = sum((c.contract_value for c in vc), Decimal("0"))
        active_count = sum(1 for c in vc if c.status == "Active")
        avg_progress = round(sum(c.progress_pct for c in vc) / len(vc))
        ev = latest_eval_by_vendor.get(vendor_name)
        if ev:
            score = _eval_score(ev.id)
            label, rcolor, rbg = rating_for(score)
            rating = f"{label} ({score:g})"
        else:
            rating, rcolor, rbg = "Not yet evaluated", "#98a2b3", "#f0f1f4"
        vendors.append(VendorSummaryItem(
            vendor=vendor_name, contractorNo=vc[0].contractor_no, contractsCount=len(vc), activeCount=active_count,
            totalValue=money(total_value), avgProgress=f"{avg_progress}%", progressColor=progress_color(avg_progress),
            rating=rating, ratingColor=rcolor, ratingBg=rbg,
        ))

    return DashboardResponse(kpis=kpis, alerts=alerts, serviceMix=service_mix, pendingActions=pending, vendors=vendors)
