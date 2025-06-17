from sqlalchemy.orm import Session
from db.base import UserTable
from db.base import User as UserModel


def get_user_tables(db: Session, *, user: UserModel):
    # Эта функция должна будет получать таблицы из БД, а не из словаря в памяти.
    # Пока что оставим ее как заглушку.
    # return db.query(UserTable).filter(UserTable.user_id == user.id).all()
    # Временная реализация, чтобы не сломать существующий код.
    # В идеале table_service должен использовать этот CRUD.
    return []
