from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.business import rating_for, score_kpi
from app.database import get_session
from app.models import Evaluation, EvaluationKpiRow
from app.schemas.evaluations import (
    EvalAdjRow,
    EvalCatBar,
    EvalKpiRow,
    EvalMetaItem,
    EvalRating,
    EvalRatingGuideRow,
    EvaluationResponse,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

TABS = [
    {"id": "jr", "label": "Construction / JR"},
    {"id": "soft", "label": "Soft Services"},
    {"id": "hard", "label": "Hard FM (MEP)"},
]
CAT_COLORS = ["#3a5bd9", "#12a679", "#7a5bd9", "#2c7fb0", "#b45309", "#c0362c", "#0f766e"]
RATING_GUIDE = [
    EvalRatingGuideRow(range="≥ 90", label="Excellent", color="#12805c"),
    EvalRatingGuideRow(range="80–89.9", label="Good", color="#177245"),
    EvalRatingGuideRow(range="70–79.9", label="Acceptable", color="#b45309"),
    EvalRatingGuideRow(range="60–69.9", label="Poor", color="#b54708"),
    EvalRatingGuideRow(range="< 60", label="Unsatisfactory", color="#c0362c"),
]


@router.get("", response_model=EvaluationResponse)
async def get_evaluation(serviceLine: str = Query("jr"), session: AsyncSession = Depends(get_session)) -> EvaluationResponse:
    result = await session.execute(
        select(Evaluation).where(Evaluation.service_line == serviceLine).order_by(Evaluation.id.desc())
    )
    evaluation = result.scalars().first()
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"No evaluation seeded for service line '{serviceLine}'")

    kpi_result = await session.execute(
        select(EvaluationKpiRow).where(EvaluationKpiRow.evaluation_id == evaluation.id).order_by(EvaluationKpiRow.id)
    )
    kpi_rows = list(kpi_result.scalars().all())

    total = 0.0
    cat_agg: dict[str, float] = {}
    cat_weight_totals: dict[str, float] = {}
    rows: list[EvalKpiRow] = []
    prev_cat = None
    for k in kpi_rows:
        sc = score_kpi(float(k.actual), float(k.target_value), k.direction)
        weight = float(k.weight)
        weighted = weight * sc / 100
        total += weighted
        cat_agg[k.category] = cat_agg.get(k.category, 0) + weighted
        cat_weight_totals[k.category] = cat_weight_totals.get(k.category, 0) + weight
        score_color = "#12805c" if sc >= 90 else ("#b45309" if sc >= 70 else "#c0362c")
        show_cat = k.category != prev_cat
        prev_cat = k.category
        if k.direction == "zero":
            actual_str = f"{float(k.actual):g}"
        else:
            actual_str = f"{float(k.actual) * 100:.1f}".rstrip("0").rstrip(".") + "%"
        rows.append(EvalKpiRow(
            cat=k.category if show_cat else "", catWeight=600 if show_cat else 400,
            kpi=k.kpi, target=k.target_label, weight=f"{weight:g}", actual=actual_str,
            score=f"{round(sc)}%", scoreColor=score_color, weighted=f"{weighted:.2f}",
        ))

    total = round(total * 10) / 10
    label, color, bg = rating_for(total)
    cats = [
        EvalCatBar(
            label=cat, val=f"{val:.1f}",
            width=f"{min(100, (val / cat_weight_totals[cat]) * 100) if cat_weight_totals[cat] else 0:.0f}%",
            color=CAT_COLORS[i % len(CAT_COLORS)],
        )
        for i, (cat, val) in enumerate(cat_agg.items())
    ]

    penalty_adj = float(evaluation.penalty_adj_pct)
    incentive_adj = float(evaluation.incentive_adj_pct)
    net_adj = penalty_adj + incentive_adj
    adj = [
        EvalAdjRow(k="Penalty (%)", v=f"{penalty_adj:g}%", w=500, c="#c0362c" if penalty_adj < 0 else "#667085"),
        EvalAdjRow(k="Incentive (%)", v=f"{incentive_adj:g}%", w=500, c="#12805c" if incentive_adj > 0 else "#667085"),
        EvalAdjRow(k="Net Adjustment", v=f"{net_adj:g}%", w=700, c="#c0362c" if net_adj < 0 else "#12805c"),
    ]

    meta = [
        EvalMetaItem(k="Subcontractor", v=evaluation.subcontractor),
        EvalMetaItem(k="Project", v=evaluation.project),
        EvalMetaItem(k="Period", v=evaluation.period),
        EvalMetaItem(k="Evaluator", v=evaluation.evaluator),
    ]

    return EvaluationResponse(
        tabs=TABS, activeTab=serviceLine, meta=meta, rows=rows, total=f"{total:g}",
        rating=EvalRating(label=label, color=color, bg=bg), cats=cats, adj=adj, ratingGuide=RATING_GUIDE,
    )
