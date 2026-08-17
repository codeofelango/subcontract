from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import ROLES, quick_login_slot, require_roles
from app.database import get_session
from app.models import AppUser
from app.schemas.users import UserIn, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _out(u: AppUser) -> UserOut:
    return UserOut(
        id=u.id, name=u.name, email=u.email, department=u.department, title=u.title,
        active=u.active, role=u.role, isQuickLogin=u.is_quick_login,
    )


def _validate_role(role: str | None) -> None:
    if role is not None and role not in ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {ROLES} or null")


async def _claim_quick_login_slot(session: AsyncSession, role: str | None, user_id: int | None) -> None:
    """Only one active row per quick-login slot (admin/requester/approver) can be flagged at a
    time - flip this one on by first flipping off whichever row currently holds that slot.
    """
    slot = quick_login_slot(role)
    if slot is None:
        raise HTTPException(status_code=422, detail="Only a user with a login role can be a quick-login account")
    result = await session.execute(select(AppUser).where(AppUser.is_quick_login.is_(True)))
    for other in result.scalars().all():
        if other.id != user_id and quick_login_slot(other.role) == slot:
            other.is_quick_login = False


@router.get("", response_model=list[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserOut]:
    result = await session.execute(select(AppUser).order_by(AppUser.name))
    return [_out(u) for u in result.scalars().all()]


@router.post("", response_model=UserOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
async def create_user(payload: UserIn, session: AsyncSession = Depends(get_session)) -> UserOut:
    _validate_role(payload.role)
    if payload.isQuickLogin:
        await _claim_quick_login_slot(session, payload.role, None)
    user = AppUser(
        name=payload.name, email=payload.email, department=payload.department,
        title=payload.title, active=payload.active, role=payload.role, is_quick_login=payload.isQuickLogin,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _out(user)


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles("admin"))])
async def update_user(user_id: int, payload: UserIn, session: AsyncSession = Depends(get_session)) -> UserOut:
    _validate_role(payload.role)
    user = await session.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.isQuickLogin:
        await _claim_quick_login_slot(session, payload.role, user_id)
    user.name = payload.name
    user.email = payload.email
    user.department = payload.department
    user.title = payload.title
    user.active = payload.active
    user.role = payload.role
    user.is_quick_login = payload.isQuickLogin
    await session.commit()
    await session.refresh(user)
    return _out(user)


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_roles("admin"))])
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)) -> None:
    user = await session.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
