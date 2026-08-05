from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    department: str
    title: str
    active: bool


class UserIn(BaseModel):
    name: str
    email: str
    department: str
    title: str
    active: bool = True
