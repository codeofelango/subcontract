from typing import Any

from pydantic import BaseModel


class WorkflowSummary(BaseModel):
    id: int
    name: str
    appliesTo: str
    isActive: bool
    stepCount: int
    createdAt: str


class WorkflowDetail(BaseModel):
    id: int
    name: str
    appliesTo: str
    isActive: bool
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class WorkflowCreateRequest(BaseModel):
    name: str
    appliesTo: str  # 'contract_scope' | 'contract_manpower' | 'change_order' | 'penalty'


class WorkflowSaveRequest(BaseModel):
    name: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
