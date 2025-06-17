from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from crud import crud_user
from schemas.token import Token
from schemas.user import User, UserCreate
from core import security
from core.deps import get_db
from core.security import verify_password
from services.avatar_service import generate_avatar


router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud_user.user.get_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "access_token": security.create_access_token(data={"sub": str(user.id)}),
        "token_type": "bearer",
    }


@router.post("/register", response_model=User)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
):
    """
    Create new user.
    """
    user = crud_user.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_user.user.create(db, obj_in=user_in)

    # Generate and assign default avatar
    avatar_url = generate_avatar(user.username)
    user.avatar_url = avatar_url
    user.is_default_avatar = True
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
