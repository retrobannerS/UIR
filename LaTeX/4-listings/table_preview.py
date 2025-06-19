import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from features.tables import crud

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
            return {"error": "Unsupported file format for preview."}

        preview = df.head(5).to_dict(orient="records")
        columns = df.columns.tolist()
        return {"preview": preview, "columns": columns, "total_rows": len(df)}

    except Exception as e:
        raise HTTPException(status_code=500, 
                            detail=f"Error reading table file: {e}")