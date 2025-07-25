from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union

from core.security import get_password_hash, verify_password
from db.base_crud import CRUDBase
from features.users.models import User
from .schemas import UserCreate, UserUpdate
from services.avatar_service import generate_avatar


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Generate default avatar before creating the user object
        avatar_url = generate_avatar(obj_in.username)

        db_obj = User(
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            avatar_url=avatar_url,
            is_default_avatar=True,
            is_superuser=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def is_active(self, user: User) -> bool:
        return user.is_active

    def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user = CRUDUser(User)
