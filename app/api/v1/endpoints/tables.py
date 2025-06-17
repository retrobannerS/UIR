from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.deps import get_current_user, get_db
from db.base import User

# Заглушки, так как table_service и text_to_sql_service будут переписаны
from services.table_service import (
    save_uploaded_file,
    get_user_tables as get_tables_from_service,
    delete_table as delete_table_from_service,
    get_table_preview,
    generate_sql_query,
)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """
    Upload a table file (CSV or Excel).
    Временная реализация через старый сервис.
    """
    return await save_uploaded_file(file, current_user)


@router.get("/")
def get_tables(current_user: User = Depends(get_current_user)):
    """
    Get list of all tables for the current user.
    Временная реализация через старый сервис.
    """
    return get_tables_from_service(current_user)


@router.delete("/{table_name}")
def remove_table(table_name: str, current_user: User = Depends(get_current_user)):
    """
    Delete a table by name.
    Временная реализация через старый сервис.
    """
    if delete_table_from_service(table_name, current_user):
        return {"message": f"Table {table_name} deleted successfully"}
    raise HTTPException(status_code=404, detail="Table not found")


@router.get("/{table_name}/preview")
def preview_table(table_name: str, current_user: User = Depends(get_current_user)):
    """Get preview of table data"""
    return get_table_preview(table_name, current_user)


@router.post("/generate-sql")
async def generate_sql(
    question: str, table_name: str, current_user: User = Depends(get_current_user)
):
    """Generate SQL from natural language query"""
    return generate_sql_query(question, table_name, current_user)
