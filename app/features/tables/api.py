from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List

from core.deps import get_db, get_current_active_user
from features.users.models import User
from features.tables import crud
from features.tables.schemas import Table, TableUpdate
from services import table_service

router = APIRouter()


@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_table_file(
    file: UploadFile = File(...),
    preview_rows: int = Form(5),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a preview of an uploaded .csv or .xlsx file, showing the
    header and the first N rows.
    """
    return await table_service.get_preview_from_upload(
        file=file, preview_rows=preview_rows
    )


@router.post("/upload", response_model=Table, status_code=status.HTTP_201_CREATED)
async def upload_table_file(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    table_name: str = Form(None),
    current_user: User = Depends(get_current_active_user),
):
    """
    Handle the upload of a .csv or .xlsx file, save it, and create a
    corresponding entry in the database for the user's table.
    A custom table name can be provided.
    """
    return await table_service.process_and_save_table(
        db=db, file=file, user=current_user, custom_table_name=table_name
    )


@router.get("/", response_model=List[Table])
def get_user_tables(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve all tables associated with the current user.
    """
    return crud.get_tables_by_user(db=db, user_id=current_user.id)


@router.delete("/{table_id}", response_model=Table)
def delete_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a user's table. This removes the file from storage and the
    entry from the database.
    """
    deleted_table = table_service.delete_table_file_and_db_entry(
        db=db, table_id=table_id, user_id=current_user.id
    )
    if not deleted_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
        )
    return deleted_table


@router.put("/{table_id}", response_model=Table)
def update_table_name(
    table_id: int,
    table_update: TableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a table's metadata, such as its name.
    """
    updated_table = table_service.rename_table(
        db=db,
        table_id=table_id,
        new_name=table_update.table_name,
        user_id=current_user.id,
    )
    if not updated_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
        )
    return updated_table


@router.get("/{table_id}/preview")
def get_table_preview(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a preview of a specific table's data, including the first 5 rows,
    column names, and total row count.
    """
    # The service function will handle user ownership check and exceptions
    return table_service.get_table_preview(
        db=db, table_id=table_id, user_id=current_user.id
    )
