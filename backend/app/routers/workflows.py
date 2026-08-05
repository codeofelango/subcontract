from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import WorkflowStepTemplate, WorkflowTemplate
from app.schemas.workflows import WorkflowCreateRequest, WorkflowDetail, WorkflowSaveRequest, WorkflowSummary

router = APIRouter(prefix="/workflows", tags=["workflows"])

APPLIES_TO_VALUES = {"contract_scope", "contract_manpower", "change_order", "penalty"}


def _ordered_node_ids(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[str]:
    """Validates the graph is a single linear chain (no branching, no cycles, no orphans) and
    returns node ids in chain order. Raises HTTPException(400) with a human-readable reason.
    """
    if not nodes:
        raise HTTPException(status_code=400, detail="A flow needs at least one step")

    node_ids = {n["id"] for n in nodes}
    indeg: Counter[str] = Counter()
    outdeg: Counter[str] = Counter()
    next_of: dict[str, str] = {}
    for e in edges:
        src, tgt = e["source"], e["target"]
        if src not in node_ids or tgt not in node_ids:
            raise HTTPException(status_code=400, detail="Edge references an unknown node")
        indeg[tgt] += 1
        outdeg[src] += 1
        next_of[src] = tgt

    if any(indeg[n["id"]] > 1 or outdeg[n["id"]] > 1 for n in nodes):
        raise HTTPException(status_code=400, detail="Branching isn't supported — each step must connect to exactly one next step")

    starts = [n["id"] for n in nodes if indeg[n["id"]] == 0]
    ends = [n["id"] for n in nodes if outdeg[n["id"]] == 0]
    if len(starts) != 1 or len(ends) != 1:
        raise HTTPException(status_code=400, detail="Steps must form a single connected chain from start to end")

    ordered = [starts[0]]
    while ordered[-1] in next_of:
        ordered.append(next_of[ordered[-1]])
    if len(ordered) != len(nodes):
        raise HTTPException(status_code=400, detail="Steps must form a single connected chain from start to end")
    return ordered


def _summary(t: WorkflowTemplate) -> WorkflowSummary:
    return WorkflowSummary(
        id=t.id, name=t.name, appliesTo=t.applies_to, isActive=t.is_active,
        stepCount=len(t.canvas_nodes or []), createdAt=t.created_at.strftime("%d %b %Y"),
    )


def _detail(t: WorkflowTemplate) -> WorkflowDetail:
    return WorkflowDetail(id=t.id, name=t.name, appliesTo=t.applies_to, isActive=t.is_active, nodes=t.canvas_nodes, edges=t.canvas_edges)


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(appliesTo: str | None = None, session: AsyncSession = Depends(get_session)) -> list[WorkflowSummary]:
    stmt = select(WorkflowTemplate).order_by(WorkflowTemplate.applies_to, WorkflowTemplate.created_at)
    if appliesTo:
        stmt = stmt.where(WorkflowTemplate.applies_to == appliesTo)
    result = await session.execute(stmt)
    return [_summary(t) for t in result.scalars().all()]


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(workflow_id: int, session: AsyncSession = Depends(get_session)) -> WorkflowDetail:
    template = await session.get(WorkflowTemplate, workflow_id)
    if not template:
        raise HTTPException(status_code=404, detail="Flow not found")
    return _detail(template)


@router.post("", response_model=WorkflowDetail, status_code=201)
async def create_workflow(payload: WorkflowCreateRequest, session: AsyncSession = Depends(get_session)) -> WorkflowDetail:
    if payload.appliesTo not in APPLIES_TO_VALUES:
        raise HTTPException(status_code=400, detail=f"appliesTo must be one of {sorted(APPLIES_TO_VALUES)}")

    start_node = {"id": "n1", "type": "step", "position": {"x": 60, "y": 120}, "data": {"label": "Raised", "userId": None}}
    template = WorkflowTemplate(name=payload.name, applies_to=payload.appliesTo, is_active=False, canvas_nodes=[start_node], canvas_edges=[])
    session.add(template)
    await session.flush()
    session.add(WorkflowStepTemplate(template_id=template.id, seq=0, role="Raised", user_id=None))
    await session.commit()
    await session.refresh(template)
    return _detail(template)


@router.put("/{workflow_id}", response_model=WorkflowDetail)
async def save_workflow(workflow_id: int, payload: WorkflowSaveRequest, session: AsyncSession = Depends(get_session)) -> WorkflowDetail:
    template = await session.get(WorkflowTemplate, workflow_id)
    if not template:
        raise HTTPException(status_code=404, detail="Flow not found")

    ordered_ids = _ordered_node_ids(payload.nodes, payload.edges)
    nodes_by_id = {n["id"]: n for n in payload.nodes}

    template.name = payload.name
    template.canvas_nodes = payload.nodes
    template.canvas_edges = payload.edges

    result = await session.execute(select(WorkflowStepTemplate).where(WorkflowStepTemplate.template_id == workflow_id))
    for step in result.scalars().all():
        await session.delete(step)
    await session.flush()

    for i, node_id in enumerate(ordered_ids):
        data = nodes_by_id[node_id].get("data", {})
        session.add(WorkflowStepTemplate(template_id=workflow_id, seq=i, role=data.get("label") or "Step", user_id=data.get("userId")))

    await session.commit()
    await session.refresh(template)
    return _detail(template)


@router.post("/{workflow_id}/activate", response_model=WorkflowDetail)
async def activate_workflow(workflow_id: int, session: AsyncSession = Depends(get_session)) -> WorkflowDetail:
    template = await session.get(WorkflowTemplate, workflow_id)
    if not template:
        raise HTTPException(status_code=404, detail="Flow not found")

    await session.execute(
        update(WorkflowTemplate).where(WorkflowTemplate.applies_to == template.applies_to).values(is_active=False)
    )
    template.is_active = True
    await session.commit()
    await session.refresh(template)
    return _detail(template)
