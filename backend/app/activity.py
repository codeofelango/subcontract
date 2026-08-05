from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLogEntry


def log_activity(
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    summary: str,
    contract_id: str | None = None,
    actor: str = "System",
) -> None:
    """Records one line in the activity log within the caller's existing session/transaction.
    Caller is still responsible for committing.
    """
    session.add(ActivityLogEntry(
        contract_id=contract_id, entity_type=entity_type, entity_id=entity_id,
        action=action, summary=summary, actor=actor,
    ))
