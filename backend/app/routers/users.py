from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import AppUser
from app.schemas.users import UserIn, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _out(u: AppUser) -> UserOut:
    return UserOut(id=u.id, name=u.name, email=u.email, department=u.department, title=u.title, active=u.active)


@router.get("", response_model=list[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserOut]:
    result = await session.execute(select(AppUser).order_by(AppUser.name))
    return [_out(u) for u in result.scalars().all()]


@router.post("", response_model=UserOut, status_code=201)
async def create_user(payload: UserIn, session: AsyncSession = Depends(get_session)) -> UserOut:
    user = AppUser(name=payload.name, email=payload.email, department=payload.department, title=payload.title, active=payload.active)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _out(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserIn, session: AsyncSession = Depends(get_session)) -> UserOut:
    user = await session.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = payload.name
    user.email = payload.email
    user.department = payload.department
    user.title = payload.title
    user.active = payload.active
    await session.commit()
    await session.refresh(user)
    return _out(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)) -> None:
    user = await session.get(AppUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
