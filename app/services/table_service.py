import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO
from typing import Optional
import logging

from features.users.models import User
from features.tables import crud
from features.tables.schemas import TableCreate, TableUpdate
from core.config import settings

logger = logging.getLogger(__name__)


def validate_and_sanitize_table_name(db: Session, user_id: int, table_name: str) -> str:
    """
    Validates the table name against business rules and checks for uniqueness.
    """
    try:
        # Use Pydantic model for validation
        validated_data = TableUpdate(table_name=table_name)
        sanitized_name = validated_data.table_name
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    # Check if a table with the same name already exists for this user
    if crud.get_table_by_name(db, user_id=user_id, table_name=sanitized_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Таблица с именем '{sanitized_name}' уже существует.",
        )
    return sanitized_name


async def process_and_save_table(
    db: Session, file: UploadFile, user: User, custom_table_name: Optional[str] = None
) -> crud.Table:
    # Basic validation for file type
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый тип файла. Пожалуйста, загрузите файл .csv или .xlsx.",
        )

    # Read content to check if file is empty
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Загруженный файл пуст.",
        )
    # Reset file pointer after reading
    await file.seek(0)

    # Specific check for Excel files to have only one sheet
    if file.filename.endswith(".xlsx"):
        xls = pd.ExcelFile(BytesIO(content))
        if len(xls.sheet_names) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel файлы с несколькими листами не поддерживаются.",
            )

    # Determine table name
    base_name = custom_table_name or os.path.splitext(file.filename)[0]

    # Validate the determined table name
    final_table_name = validate_and_sanitize_table_name(
        db, user_id=user.id, table_name=base_name
    )

    # Create a unique path for the file
    user_upload_dir = os.path.join(settings.UPLOADS_DIR, "tables", str(user.id))
    os.makedirs(user_upload_dir, exist_ok=True)

    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(user_upload_dir, unique_filename)

    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)  # Use the content we've already read
    except Exception as e:
        # Clean up if file writing fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сохранить файл: {e}",
        )
    finally:
        file.file.close()

    # Create the table entry in the database
    table_create = TableCreate(
        table_name=final_table_name,
        original_file_name=original_filename,
        file_path=file_path,
        user_id=user.id,
    )

    return crud.create_user_table(db, table=table_create)


async def get_preview_from_upload(file: UploadFile, preview_rows: int = 5) -> dict:
    """
    Reads the first N rows of an uploaded .csv or .xlsx file for preview.
    """
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый тип файла. Пожалуйста, загрузите файл .csv или .xlsx.",
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Загруженный файл пуст.",
            )

        file_stream = BytesIO(content)

        if file.filename.endswith(".csv"):
            df = pd.read_csv(file_stream)
        else:  # .xlsx
            # Check for multiple sheets in excel file
            xls = pd.ExcelFile(file_stream)
            if len(xls.sheet_names) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Excel файлы с несколькими листами не поддерживаются.",
                )
            df = pd.read_excel(xls, sheet_name=xls.sheet_names[0], engine="openpyxl")

        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл не содержит данных.",
            )

        # Limit to N rows for preview
        preview_df = df.head(preview_rows)

        # Get header
        header = preview_df.columns.tolist()

        # Get data rows
        data = preview_df.values.tolist()

        return {"header": header, "data": data}

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Загруженный файл пуст или не содержит данных.",
        )
    except Exception as e:
        logger.error(f"Error reading file for preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось обработать файл. Возможно, он поврежден или имеет неверный формат.",
        )
    finally:
        await file.seek(0)  # Reset file pointer in case it's used again


def rename_table(db: Session, table_id: int, new_name: str, user_id: int) -> crud.Table:
    """
    Renames a table for a given user.
    """
    # First, validate the new name
    validated_new_name = validate_and_sanitize_table_name(
        db, user_id=user_id, table_name=new_name
    )

    # Then, update the table name in the database
    return crud.update_table_name(
        db=db, table_id=table_id, new_name=validated_new_name, user_id=user_id
    )


def delete_table_file_and_db_entry(
    db: Session, table_id: int, user_id: int
) -> crud.Table:
    # First, get the table to find its file path
    table_to_delete = (
        db.query(crud.Table)
        .filter(crud.Table.id == table_id, crud.Table.user_id == user_id)
        .first()
    )

    if not table_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
        )

    file_path = table_to_delete.file_path

    # Delete the database entry
    deleted_table = crud.delete_table(db=db, table_id=table_id, user_id=user_id)

    # If DB deletion was successful, delete the file
    if deleted_table and file_path and os.path.exists(file_path):
        os.remove(file_path)

    return deleted_table


def get_table_preview(db: Session, table_id: int, user_id: int) -> dict:
    table = (
        db.query(crud.Table)
        .filter(crud.Table.id == table_id, crud.Table.user_id == user_id)
        .first()
    )
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Table not found"
        )

    try:
        if table.file_path.endswith(".csv"):
            df = pd.read_csv(table.file_path)
        elif table.file_path.endswith(".xlsx"):
            df = pd.read_excel(table.file_path)
        else:
            return {"error": "Неподдерживаемый формат файла для предпросмотра."}

        preview = df.head(5).to_dict(orient="records")
        columns = df.columns.tolist()
        return {"preview": preview, "columns": columns, "total_rows": len(df)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения файла таблицы: {e}")
