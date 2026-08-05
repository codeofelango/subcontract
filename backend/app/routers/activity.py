from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ActivityLogEntry
from app.schemas.activity import ActivityEntryOut, AskActivityRequest, AskActivityResponse

router = APIRouter(prefix="/activity", tags=["activity"])

# Scan window for keyword matching - the log is small enough in this module's scope that a full
# table scan per question is fine; a real deployment would push this filtering into SQL/full-text search.
SCAN_LIMIT = 1000
STOPWORDS = {"the", "and", "for", "was", "what", "who", "did", "has", "have", "any", "all", "with", "this", "that"}


def _to_out(e: ActivityLogEntry) -> ActivityEntryOut:
    return ActivityEntryOut(
        id=e.id, contractId=e.contract_id, entityType=e.entity_type, entityId=e.entity_id,
        action=e.action, summary=e.summary, actor=e.actor, createdAt=e.created_at.strftime("%d %b %Y, %H:%M"),
    )


@router.get("", response_model=list[ActivityEntryOut])
async def list_activity(limit: int = 30, contractId: str | None = None, session: AsyncSession = Depends(get_session)) -> list[ActivityEntryOut]:
    stmt = select(ActivityLogEntry)
    if contractId:
        stmt = stmt.where(ActivityLogEntry.contract_id == contractId)
    stmt = stmt.order_by(ActivityLogEntry.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return [_to_out(e) for e in result.scalars().all()]


@router.post("/ask", response_model=AskActivityResponse)
async def ask_activity(payload: AskActivityRequest, session: AsyncSession = Depends(get_session)) -> AskActivityResponse:
    """Answers a free-text question about actions taken in the module via keyword matching over the
    activity log - no embeddings/vector search (out of scope for now, see CLAUDE.md).
    """
    words = [w.strip(".,?!").lower() for w in payload.question.split()]
    words = [w for w in words if len(w) > 2 and w not in STOPWORDS]

    result = await session.execute(select(ActivityLogEntry).order_by(ActivityLogEntry.created_at.desc()).limit(SCAN_LIMIT))
    entries = result.scalars().all()

    def score(e: ActivityLogEntry) -> int:
        haystack = f"{e.summary} {e.entity_type} {e.action} {e.contract_id or ''}".lower()
        return sum(1 for w in words if w in haystack)

    scored = sorted(((score(e), e) for e in entries), key=lambda pair: (-pair[0], -pair[1].id))
    matches = [e for s, e in scored if s > 0][:10]

    if not words or not matches:
        fallback = list(entries[:5])
        return AskActivityResponse(
            answer="I couldn't find a specific match for that — here's the most recent activity instead." if words else
                   "Ask about a contract, vendor, IPC, change order, or penalty and I'll search the activity log.",
            matches=[_to_out(e) for e in fallback],
        )

    return AskActivityResponse(answer=f"Found {len(matches)} matching action(s).", matches=[_to_out(e) for e in matches])
