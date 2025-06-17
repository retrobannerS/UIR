import sys
import os

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.session import SessionLocal
from db.models.user import User
from db.models.table import UserTable  # noqa


def delete_all_users():
    db = SessionLocal()
    try:
        num_rows_deleted = db.query(User).delete()
        db.commit()
        print(f"Successfully deleted {num_rows_deleted} users.")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("This script will delete all users from the database.")
    confirmation = input("Are you sure you want to continue? (y/n): ")
    if confirmation.lower() == "y":
        delete_all_users()
    else:
        print("Operation cancelled.")
 