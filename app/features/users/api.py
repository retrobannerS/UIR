from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Response,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from datetime import timedelta
import shutil
import os
import re
from pathlib import Path
import uuid

from features.users import crud
from features.users.schemas import (
    User,
    UserCreate,
    UserUpdate,
    Token,
    UsernameCheck,
    UserPasswordUpdate,
)
from .models import User as UserModel
from core import security
from core.deps import get_db, get_current_active_user
from core.config import settings
from services.avatar_service import generate_avatar

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


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
            detail="Username can only contain alphanumeric characters and underscores.",
        )

    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = crud.user.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
) -> Any:
    """
    Get current user.
    """
    db.refresh(current_user)  # This line is crucial
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
) -> Any:
    """
    Update own user.
    """
    update_data = user_in.dict(exclude_unset=True)

    # Handling username change
    if "username" in update_data and update_data["username"] != current_user.username:
        new_username = update_data["username"]

        # Validate username format
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", new_username):
            raise HTTPException(
                status_code=422,
                detail="Invalid username format. Use 3-20 alphanumeric characters or underscores.",
            )

        # Check if new username is already taken
        existing_user = crud.user.get_by_username(db, username=new_username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Username already exists",
            )

        # If the user has a default avatar, it should be regenerated
        if current_user.is_default_avatar:
            old_avatar_path_str = current_user.avatar_url.lstrip("/")
            old_avatar_path = Path(old_avatar_path_str)

            # Generate a new default avatar and delete the old one
            new_avatar_url = generate_avatar(new_username)
            update_data["avatar_url"] = new_avatar_url
            if old_avatar_path.exists():
                os.remove(old_avatar_path)
        # If the avatar is custom, we do nothing to it. It's filename is not tied to the username.

    updated_user = crud.user.update(db, db_obj=current_user, obj_in=update_data)

    return updated_user


@router.put("/me/username", response_model=User)
def update_username(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
):
    """
    Update own username.
    """
    new_username = user_in.username
    if new_username == current_user.username:
        return current_user

    # Validate username format
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", new_username):
        raise HTTPException(
            status_code=422,
            detail="Invalid username format. Use 3-20 alphanumeric characters or underscores.",
        )

    # Check if new username is already taken
    existing_user = crud.user.get_by_username(db, username=new_username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    update_data = {"username": new_username}

    # If the user has a default avatar, it should be regenerated
    if current_user.is_default_avatar and current_user.avatar_url:
        old_avatar_path_str = current_user.avatar_url.lstrip("/")
        old_avatar_path = Path(old_avatar_path_str)
        if old_avatar_path.exists():
            try:
                os.remove(old_avatar_path)
            except OSError as e:
                # Log the error, but don't block the username change
                print(f"Error removing old avatar: {e}")

        new_avatar_url = generate_avatar(new_username)
        update_data["avatar_url"] = new_avatar_url

    updated_user = crud.user.update(db, db_obj=current_user, obj_in=update_data)

    return updated_user


@router.put("/me/avatar", response_model=User)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
    db: Session = Depends(get_db),
):
    """
    Upload a user avatar.
    """
    # Delete old avatar if it exists
    if current_user.avatar_url:
        old_avatar_path = current_user.avatar_url.lstrip("/")
        if os.path.exists(old_avatar_path):
            os.remove(old_avatar_path)

    file_extension = Path(file.filename).suffix
    if file_extension.lower() not in [".png", ".jpg", ".jpeg"]:
        raise HTTPException(
            status_code=400, detail="Invalid image format. Use PNG, JPG, or JPEG."
        )

    # Save new avatar with a unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"uploads/avatars/{unique_filename}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    avatar_url = f"/{file_path}"
    update_data = {"avatar_url": avatar_url, "is_default_avatar": False}

    updated_user = crud.user.update(db, db_obj=current_user, obj_in=update_data)

    return updated_user


@router.delete("/me/avatar", response_model=User)
def delete_avatar(
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
    db: Session = Depends(get_db),
):
    """
    Delete a user's custom avatar and revert to the default.
    """
    # If the user already has a default avatar, do nothing.
    if current_user.is_default_avatar:
        return current_user

    # Delete old custom avatar if it exists
    if current_user.avatar_url:
        old_avatar_path = current_user.avatar_url.lstrip("/")
        if os.path.exists(old_avatar_path):
            os.remove(old_avatar_path)

    # Generate a new default avatar
    default_avatar_path = generate_avatar(current_user.username)
    update_data = {"avatar_url": default_avatar_path, "is_default_avatar": True}
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=update_data)

    return updated_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    *,
    db: Session = Depends(get_db),
    password_update: UserPasswordUpdate,
    current_user: UserModel = Depends(get_current_active_user, use_cache=False),
):
    """
    Update user's password.
    """
    if not security.verify_password(
        password_update.old_password, current_user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Validate new password
    new_password = password_update.new_password
    if not re.match(r"^[a-zA-Z0-9]*$", new_password):
        raise HTTPException(
            status_code=422, detail="Password can only contain alphanumeric characters."
        )
    if not (8 <= len(new_password) <= 20):
        raise HTTPException(
            status_code=422, detail="Password must be between 8 and 20 characters."
        )
    if not re.search(r"\d", new_password):
        raise HTTPException(
            status_code=422, detail="Password must contain at least one number."
        )

    hashed_password = security.get_password_hash(new_password)
    current_user.hashed_password = hashed_password
    db.add(current_user)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/check-username", response_model=UsernameCheck)
def check_username_exists(username: str, db: Session = Depends(get_db)):
    """
    Check if a username already exists.
    """
    user = crud.user.get_by_username(db, username=username)
    return {"exists": user is not None}
