import pandas as pd
from typing import List, Dict
import os
from fastapi import UploadFile
import logging
from db.base import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TableService:
    def __init__(self):
        # Dictionary to store tables by username and table_name
        self.tables: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"TableService initialized. Upload directory: {self.upload_dir}")

    async def save_uploaded_file(self, file: UploadFile, user: User) -> dict:
        """Upload and process a table file (CSV or Excel) for a specific user"""
        logger.info(
            f"Processing file upload: {file.filename} for user: {user.username}"
        )

        file_path = os.path.join(self.upload_dir, file.filename)
        logger.info(f"Temporary file path: {file_path}")

        try:
            # Save the file temporarily
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            logger.info(f"File saved temporarily at: {file_path}")

            # Read the file based on its extension
            if file.filename.endswith(".csv"):
                logger.info("Reading CSV file")
                df = pd.read_csv(file_path)
            elif file.filename.endswith((".xlsx", ".xls")):
                logger.info("Reading Excel file")
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")

            # Store the table for the user
            table_name = os.path.splitext(file.filename)[0]
            if user.username not in self.tables:
                self.tables[user.username] = {}
            self.tables[user.username][table_name] = df
            logger.info(
                f"Table '{table_name}' loaded successfully for user {user.username}. Shape: {df.shape}"
            )

            # Clean up the temporary file
            os.remove(file_path)
            logger.info(f"Temporary file removed: {file_path}")

            return {"message": "Table uploaded successfully", "table_name": table_name}

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            # Clean up the temporary file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    def get_user_tables(self, user: User) -> List[Dict[str, str]]:
        """Get list of all tables for a specific user"""
        if user.username not in self.tables:
            return []
        tables = [{"name": name} for name in self.tables[user.username].keys()]
        logger.info(
            f"Returning {len(tables)} tables for user {user.username}: {[t['name'] for t in tables]}"
        )
        return tables

    def delete_table(self, table_name: str, user: User) -> bool:
        """Delete a table by name for a specific user"""
        logger.info(
            f"Attempting to delete table: {table_name} for user: {user.username}"
        )
        if user.username in self.tables and table_name in self.tables[user.username]:
            del self.tables[user.username][table_name]
            logger.info(
                f"Table '{table_name}' deleted successfully for user {user.username}"
            )
            return True
        logger.warning(f"Table '{table_name}' not found for user {user.username}")
        return False

    def get_table_preview(self, table_name: str, user: User) -> dict:
        """Get a preview of a specific table"""
        logger.info(
            f"Getting preview for table: {table_name} for user: {user.username}"
        )
        if user.username in self.tables and table_name in self.tables[user.username]:
            df = self.tables[user.username][table_name]
            preview = df.head(5).to_dict(orient="records")
            columns = df.columns.tolist()
            return {"preview": preview, "columns": columns, "total_rows": len(df)}
        return None

    def generate_sql_query(self, question: str, table_name: str, user: User) -> dict:
        """Generate SQL query from natural language question"""
        if (
            user.username not in self.tables
            or table_name not in self.tables[user.username]
        ):
            raise ValueError(f"Table {table_name} not found")

        # For now, return a simple SELECT query
        # TODO: Implement actual text-to-SQL generation
        return {
            "sql_query": f"SELECT * FROM {table_name} LIMIT 5",
            "explanation": "This is a simple preview query. Text-to-SQL generation will be implemented later.",
        }


# Create a singleton instance
table_service = TableService()

# Export the functions that will be used in routes
save_uploaded_file = table_service.save_uploaded_file
get_user_tables = table_service.get_user_tables
delete_table = table_service.delete_table
get_table_preview = table_service.get_table_preview
generate_sql_query = table_service.generate_sql_query
