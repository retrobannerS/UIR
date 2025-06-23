from typing import List, Optional
from sqlalchemy.orm import Session
from features.users.models import User
from db.base_crud import CRUDBase
from features.tables.models import Table
from features.tables.schemas import TableCreate, TableUpdate

from fastapi.encoders import jsonable_encoder


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TableCreate, user_id: int
    ) -> Table:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Table]:
        return (
            db.query(self.model)
            .filter(Table.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


table = CRUDTable(Table)


def get_table_by_name(db: Session, user_id: int, table_name: str) -> Optional[Table]:
    """
    Get a specific table by its name for a given user.
    """
    return (
        db.query(Table)
        .filter(Table.user_id == user_id, Table.table_name == table_name)
        .first()
    )


def get_tables_by_user(db: Session, user_id: int) -> list[Table]:
    """
    Get all tables owned by a specific user.
    """
    return db.query(Table).filter(Table.user_id == user_id).all()


def create_user_table(db: Session, table: TableCreate) -> Table:
    """
    Create a new table record in the database.
    """
    db_table = Table(**table.model_dump())
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table


def delete_table(db: Session, table_id: int, user_id: int) -> Optional[Table]:
    """
    Delete a table from the database by its ID, ensuring it belongs to the user.
    """
    db_table = (
        db.query(Table).filter(Table.id == table_id, Table.user_id == user_id).first()
    )
    if db_table:
        db.delete(db_table)
        db.commit()
    return db_table


def update_table_name(
    db: Session, table_id: int, new_name: str, user_id: int
) -> Optional[Table]:
    """
    Update the name of a table, ensuring it belongs to the user.
    """
    db_table = (
        db.query(Table).filter(Table.id == table_id, Table.user_id == user_id).first()
    )
    if db_table:
        db_table.table_name = new_name
        db.commit()
        db.refresh(db_table)
    return db_table
