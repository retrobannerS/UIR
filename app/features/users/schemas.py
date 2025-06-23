from pydantic import BaseModel, constr
from typing import Optional, List
from features.tables.schemas import Table


# Shared properties
class UserBase(BaseModel):
    username: Optional[constr(min_length=3, max_length=20)] = None
    email: Optional[str] = None


# Properties to receive on user creation
class UserCreate(UserBase):
    username: constr(min_length=3, max_length=20)
    password: str


# Properties to return to client
class UserInDBBase(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_default_avatar: bool = True

    model_config = {"from_attributes": True}


class User(UserInDBBase):
    tables: List[Table] = []


# Properties to receive on user update
class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    avatar_url: Optional[str] = None
    is_default_avatar: Optional[bool] = None


# Combined User model for DB representation
class UserInDB(UserInDBBase):
    hashed_password: str


class UsernameCheck(BaseModel):
    exists: bool


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None
