import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db import SessionLocal, engine, Base
from app.models import Document, Page, Block
from sqlalchemy import text

def reset_db():
    print("Resetting database...")
    db = SessionLocal()
    try:
        # Delete all rows from tables
        # Order matters due to foreign keys: Block -> Page -> Document
        db.query(Block).delete()
        db.query(Page).delete()
        db.query(Document).delete()
        db.commit()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"Error resetting database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_db()
