from pydantic import BaseModel, ConfigDict, constr, field_validator
from typing import Optional
import re

# Здесь будут схемы для таблиц, например, для их переименования или отображения.
# Пока оставим пустым.


# --- Base Schemas ---
class TableBase(BaseModel):
    table_name: str
    description: Optional[str] = None


# --- Schemas for API Operations ---


# Schema for creating a new table entry in the database.
# This is used internally after a file is uploaded.
class TableCreate(TableBase):
    original_file_name: str
    file_path: str
    user_id: int


# Schema for updating an existing table's metadata (e.g., renaming).
class TableUpdate(BaseModel):
    table_name: Optional[constr(strip_whitespace=True, min_length=3, max_length=50)] = (
        None
    )
    description: Optional[str] = None

    @field_validator("table_name", mode="before")
    def validate_table_name(cls, value):
        if value is None:
            return None  # Allow optional field
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError(
                "Имя таблицы может содержать только латинские буквы, цифры и символ подчеркивания."
            )
        return value


# --- Schemas for API Responses ---


# Base schema for representing a table from the database.
class TableInDBBase(TableBase):
    id: int
    user_id: int
    original_file_name: str

    model_config = ConfigDict(from_attributes=True)


# The schema that will be returned to the client in API responses.
class Table(TableInDBBase):
    pass


# Properties stored in DB
class TableInDB(TableInDBBase):
    pass
