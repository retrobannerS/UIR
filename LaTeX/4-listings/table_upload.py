from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from core.deps import get_db, get_current_active_user
from features.users.models import User
from features.tables.schemas import Table
from services import table_service

router = APIRouter()

@router.post("/upload", response_model=Table, 
             status_code=status.HTTP_201_CREATED,
             )
async def upload_table_file(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    Handle the upload of a .csv or .xlsx file, save it, and create a
    corresponding entry in the database for the user's table.
    """
    return await table_service.process_and_save_table(
        db=db, file=file, user=current_user
    )