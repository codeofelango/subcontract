from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models import AppUser
from app.pending import pending_actions
from app.schemas.dashboard import PendingActionItem

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/mine", response_model=list[PendingActionItem])
async def list_my_approvals(
    session: AsyncSession = Depends(get_session), current_user: AppUser = Depends(get_current_user)
) -> list[PendingActionItem]:
    return await pending_actions(session, current_user)
