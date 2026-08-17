import datetime
import logging

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import AppUser, Contract

logger = logging.getLogger(__name__)

ROLES = ("admin", "procurement_requester", "hr_requester", "approver")

# Quick-login buttons on the login screen collapse the two requester roles into one slot - a
# tester picks "Requester" and gets whichever requester account an admin has flagged, regardless
# of which department it belongs to.
QUICK_LOGIN_SLOTS = ("admin", "requester", "approver")


def quick_login_slot(role: str | None) -> str | None:
    if role == "admin":
        return "admin"
    if role in ("procurement_requester", "hr_requester"):
        return "requester"
    if role == "approver":
        return "approver"
    return None


def create_access_token(user: AppUser) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> AppUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await session.get(AppUser, int(payload["sub"]))
    if not user or not user.active or not user.role:
        raise HTTPException(status_code=403, detail="Account no longer has access - contact an Admin")
    return user


def require_roles(*roles: str):
    async def _check(current_user: AppUser = Depends(get_current_user)) -> AppUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="You don't have permission to perform this action")
        return current_user

    return _check


def assert_contract_visible(current_user: AppUser, contract: Contract) -> None:
    """Requesters only see the department that owns their contract type - Scope/Works is
    procurement's, Manpower Supply is HR's. Admin and approver need to see everything to search
    across and act on any pending item.
    """
    if current_user.role in ("admin", "approver"):
        return
    if current_user.role == "procurement_requester" and contract.contract_type == "scope":
        return
    if current_user.role == "hr_requester" and contract.contract_type == "manpower":
        return
    raise HTTPException(status_code=403, detail="You don't have access to this contract's data")
