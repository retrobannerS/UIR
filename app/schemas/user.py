from pydantic import BaseModel, Field, EmailStr
from typing import Optional


# Shared properties
class UserBase(BaseModel):
    username: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None


# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=1)


# Properties to return to client
class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    is_default_avatar: bool

    class Config:
        from_attributes = True


# Properties to receive on user update
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    avatar_url: Optional[str] = None
    is_default_avatar: Optional[bool] = None


# Combined User model for DB representation
class UserInDB(User):
    hashed_password: str


class UsernameCheck(BaseModel):
    exists: bool


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str
