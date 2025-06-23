"""
A script to synchronize the database with the filesystem using standard synchronous DB calls.

It performs the following actions:
1. Deletes table records from the database if their corresponding files are missing from the filesystem.
2. Resets user avatars to default if their avatar files are missing.
3. Deletes orphan table and avatar files from the filesystem that are not referenced in the database.
"""

import os
import logging
import sys
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.session import engine
from features.users.models import User
from features.tables.models import Table
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Use standard synchronous session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def sync_database_and_files_sync():
    """
    Main function to perform the synchronization using synchronous calls.
    """
    logging.info(
        "Starting SYNCHRONOUS synchronization between database and filesystem..."
    )
    db = SessionLocal()
    try:
        # --- 1. Sync User Avatars ---
        logging.info("Step 1: Synchronizing user avatars...")
        users = (
            db.execute(select(User).where(User.avatar_url.isnot(None))).scalars().all()
        )

        db_avatar_files = set()

        for user in users:
            if user.avatar_url:
                avatar_filename = os.path.basename(user.avatar_url)
                db_avatar_files.add(avatar_filename)

                full_path = os.path.join(
                    settings.UPLOADS_DIR, "avatars", avatar_filename
                )
                if not os.path.exists(full_path):
                    logging.warning(
                        f"Missing avatar file for user '{user.username}': {full_path}. Resetting to default."
                    )
                    user.avatar_url = None
                    user.is_default_avatar = True
                    db.add(user)

        # --- 2. Sync Tables ---
        logging.info("Step 2: Synchronizing tables...")
        tables = db.execute(select(Table)).scalars().all()
        db_table_files = {t.file_path for t in tables}

        tables_to_delete_ids = [
            table.id
            for table in tables
            if not os.path.exists(
                os.path.join(settings.UPLOADS_DIR, "tables", table.file_path)
            )
        ]

        if tables_to_delete_ids:
            logging.info(
                f"Deleting {len(tables_to_delete_ids)} orphan table records..."
            )
            db.execute(delete(Table).where(Table.id.in_(tables_to_delete_ids)))

        # --- 3. Clean up orphan files ---
        logging.info("Step 3: Cleaning up orphan files...")

        # Avatars
        avatars_dir = os.path.join(settings.UPLOADS_DIR, "avatars")
        if os.path.exists(avatars_dir):
            fs_avatars = set(os.listdir(avatars_dir))
            db_avatars_from_users = {
                os.path.basename(u.avatar_url) for u in users if u.avatar_url
            }
            orphan_avatars = fs_avatars - db_avatars_from_users
            for filename in orphan_avatars:
                logging.info(f"Deleting orphan avatar: {filename}")
                os.remove(os.path.join(avatars_dir, filename))

        # Tables
        tables_dir = os.path.join(settings.UPLOADS_DIR, "tables")
        if os.path.exists(tables_dir):
            fs_tables = set(os.listdir(tables_dir))
            orphan_tables = fs_tables - db_table_files
            for filename in orphan_tables:
                logging.info(f"Deleting orphan table file: {filename}")
                os.remove(os.path.join(tables_dir, filename))

        db.commit()
        logging.info("Synchronization commit successful.")

    except Exception as e:
        db.rollback()
        logging.error(f"An error occurred during synchronization: {e}", exc_info=True)
    finally:
        db.close()
        logging.info("Synchronization process finished.")


if __name__ == "__main__":
    # Ensure the necessary upload directories exist before running
    os.makedirs(os.path.join(settings.UPLOADS_DIR, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOADS_DIR, "tables"), exist_ok=True)
    sync_database_and_files_sync()
