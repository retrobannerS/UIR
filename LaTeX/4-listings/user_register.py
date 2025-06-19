from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import re

from features.users import crud
from features.users.schemas import User, UserCreate
from core.deps import get_db

router = APIRouter()

@router.post("/register", response_model=User)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user and return it.
    """
    # Basic validation for username and password length
    if not (3 <= len(user_in.username) <= 20):
        raise HTTPException(
            status_code=422,
            detail="Username must be between 3 and 20 characters.",
        )
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters.",
        )
    if not re.match(r"^[a-zA-Z0-9_]+$", user_in.username):
        raise HTTPException(
            status_code=422,
            detail="Username can only contain alphanumeric characters and " \
            "underscores.",
        )

    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = crud.user.create(db, obj_in=user_in)
    return user