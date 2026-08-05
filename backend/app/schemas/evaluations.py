from pydantic import BaseModel


class EvalMetaItem(BaseModel):
    k: str
    v: str


class EvalKpiRow(BaseModel):
    cat: str
    catWeight: int
    kpi: str
    target: str
    weight: str
    actual: str
    score: str
    scoreColor: str
    weighted: str


class EvalCatBar(BaseModel):
    label: str
    val: str
    width: str
    color: str


class EvalAdjRow(BaseModel):
    k: str
    v: str
    w: int
    c: str


class EvalRatingGuideRow(BaseModel):
    range: str
    label: str
    color: str


class EvalRating(BaseModel):
    label: str
    color: str
    bg: str


class EvaluationResponse(BaseModel):
    tabs: list[dict]
    activeTab: str
    meta: list[EvalMetaItem]
    rows: list[EvalKpiRow]
    total: str
    rating: EvalRating
    cats: list[EvalCatBar]
    adj: list[EvalAdjRow]
    ratingGuide: list[EvalRatingGuideRow]
