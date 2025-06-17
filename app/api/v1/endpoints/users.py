from typing import Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Response,
    status,
)
from sqlalchemy.orm import Session
import shutil
import os
import re
from pathlib import Path
import uuid

from crud import crud_user
from schemas.user import User, UserUpdate, UsernameCheck, UserPasswordUpdate
from schemas.token import Token
from core import deps
from db.models.user import User as UserModel
from services.avatar_service import generate_avatar
from core.security import get_password_hash, verify_password

router = APIRouter()


@router.get("/me", response_model=User)
def read_user_me(
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
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
        existing_user = crud_user.user.get_by_username(db, username=new_username)
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

    updated_user = crud_user.user.update(db, db_obj=current_user, obj_in=update_data)

    db.refresh(current_user)
    return updated_user


@router.put("/me/avatar", response_model=User)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
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

    updated_user = crud_user.user.update(db, db_obj=current_user, obj_in=update_data)

    return updated_user


@router.delete("/me/avatar", response_model=User)
def delete_avatar(
    current_user: UserModel = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
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
    updated_user = crud_user.user.update(db, db_obj=current_user, obj_in=update_data)

    db.refresh(current_user)
    return updated_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    *,
    db: Session = Depends(deps.get_db),
    password_update: UserPasswordUpdate,
    current_user: UserModel = Depends(deps.get_current_active_user),
):
    """
    Update user's password.
    """
    if not verify_password(password_update.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    hashed_password = get_password_hash(password_update.new_password)
    current_user.hashed_password = hashed_password
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/check-username", response_model=UsernameCheck)
def check_username_exists(username: str, db: Session = Depends(deps.get_db)):
    """
    Check if a username is available.
    """
    user = crud_user.user.get_by_username(db, username=username)
    return {"exists": bool(user)}
