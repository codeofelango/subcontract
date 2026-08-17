from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import QUICK_LOGIN_SLOTS, create_access_token, get_current_user, quick_login_slot
from app.config import settings
from app.database import get_session
from app.models import AppUser
from app.schemas.users import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

QUICK_LOGIN_LABELS = {"admin": "Admin", "requester": "Requester", "approver": "Approver"}


class MicrosoftExchangeRequest(BaseModel):
    email: str


class MicrosoftExchangeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class QuickLoginOption(BaseModel):
    slot: str
    label: str
    user: UserOut | None


class QuickLoginOptionsResponse(BaseModel):
    enabled: bool
    options: list[QuickLoginOption]


class QuickLoginRequest(BaseModel):
    slot: str


def _user_out(u: AppUser) -> UserOut:
    return UserOut(
        id=u.id, name=u.name, email=u.email, department=u.department, title=u.title,
        active=u.active, role=u.role, isQuickLogin=u.is_quick_login,
    )


@router.post("/microsoft/exchange", response_model=MicrosoftExchangeResponse)
async def exchange_microsoft_login(
    payload: MicrosoftExchangeRequest,
    x_internal_secret: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> MicrosoftExchangeResponse:
    """Called server-to-server by the Next.js NextAuth callback right after Microsoft verifies the
    user's identity - never reachable from a browser directly, since it requires the shared
    internal secret. Resolves the verified email to an AppUser with an assigned access role and
    mints our own short-lived JWT for subsequent API calls.
    """
    if not x_internal_secret or x_internal_secret != settings.internal_auth_secret:
        raise HTTPException(status_code=401, detail="Invalid internal secret")

    result = await session.execute(
        select(AppUser)
        .where(AppUser.email == payload.email, AppUser.active.is_(True), AppUser.role.is_not(None))
        .order_by(AppUser.id)
        .limit(1)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=403, detail="Your account isn't set up yet - contact an Admin to be added to the User Master with a role")

    return MicrosoftExchangeResponse(access_token=create_access_token(user), user=_user_out(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: AppUser = Depends(get_current_user)) -> UserOut:
    return _user_out(current_user)


@router.get("/quick-login/options", response_model=QuickLoginOptionsResponse)
async def quick_login_options(session: AsyncSession = Depends(get_session)) -> QuickLoginOptionsResponse:
    """Lists the 3 quick-login slots (Admin/Requester/Approver) and whichever active user an
    admin has currently flagged for each, so the login screen can show real names and grey out
    any slot nobody has been assigned to yet.
    """
    if not settings.enable_quick_login:
        return QuickLoginOptionsResponse(enabled=False, options=[])

    result = await session.execute(select(AppUser).where(AppUser.is_quick_login.is_(True), AppUser.active.is_(True)))
    by_slot = {quick_login_slot(u.role): u for u in result.scalars().all()}
    return QuickLoginOptionsResponse(
        enabled=True,
        options=[QuickLoginOption(slot=slot, label=QUICK_LOGIN_LABELS[slot], user=_user_out(by_slot[slot]) if slot in by_slot else None) for slot in QUICK_LOGIN_SLOTS],
    )


@router.post("/quick-login", response_model=MicrosoftExchangeResponse)
async def quick_login(payload: QuickLoginRequest, session: AsyncSession = Depends(get_session)) -> MicrosoftExchangeResponse:
    """Test-only sign-in that skips Microsoft entirely, minting the same JWT a real login would.
    Only ever reachable when ENABLE_QUICK_LOGIN is on - keep that false in production.
    """
    if not settings.enable_quick_login:
        raise HTTPException(status_code=403, detail="Quick login is disabled")
    if payload.slot not in QUICK_LOGIN_SLOTS:
        raise HTTPException(status_code=422, detail=f"slot must be one of {QUICK_LOGIN_SLOTS}")

    result = await session.execute(select(AppUser).where(AppUser.is_quick_login.is_(True), AppUser.active.is_(True)))
    user = next((u for u in result.scalars().all() if quick_login_slot(u.role) == payload.slot), None)
    if not user:
        raise HTTPException(status_code=404, detail="No quick-login account is set for this role yet - assign one on the Users page")

    return MicrosoftExchangeResponse(access_token=create_access_token(user), user=_user_out(user))
