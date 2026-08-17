from pydantic import BaseModel

Role = str | None  # 'admin' | 'procurement_requester' | 'hr_requester' | 'approver' | None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    department: str
    title: str
    active: bool
    role: Role
    isQuickLogin: bool


class UserIn(BaseModel):
    name: str
    email: str
    department: str
    title: str
    active: bool = True
    role: Role = None
    isQuickLogin: bool = False
