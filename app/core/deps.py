from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.config import settings
from features.users import crud as users_crud
from features.users.models import User
from db.session import get_db
from features.users.schemas import TokenData


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login/access-token")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenData(**payload)
    except (jwt.JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    try:
        user_id = int(token_data.sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token subject",
        )
    user = users_crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not users_crud.user.is_active(current_user):
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not users_crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
