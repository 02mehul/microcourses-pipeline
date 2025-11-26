import sys
import os
import asyncio

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db import SessionLocal
from app.models import Document, Block
from app.services.pipeline import process_document

from app.services.storage import upload_fileobj
import io

async def test_local():
    db = SessionLocal()
async def test_local():
    db = SessionLocal()
    try:
        # Resolve paths relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))
        pdf_path = os.path.join(project_root, "docs/dwr-25-40-2.pdf")
        
        if not os.path.exists(pdf_path):
            print(f"File {pdf_path} not found locally.")
            return

        with open(pdf_path, "rb") as f:
            file_data = f.read()
            
        storage_path = "docs/test_local.pdf"
        upload_fileobj(io.BytesIO(file_data), storage_path)
        print(f"Uploaded {pdf_path} to MinIO at {storage_path}")

        # Create a dummy document
        doc = Document(
            filename="test.pdf",
            storage_path=storage_path, 
            status="PENDING"
        )
        db.add(doc)
        db.commit()
        print(f"Created doc {doc.id}")
        
        # Run pipeline
        # Note: process_document is async
        await process_document(doc.id)
        
        # Check blocks
        blocks = db.query(Block).filter(Block.page_id.in_([p.id for p in doc.pages])).all()
        print(f"Total blocks: {len(blocks)}")
        for b in blocks:
            print(f"Block type: {b.type}, Role: {b.semantic_role}")
            print(f"Text preview: {b.text_raw[:50]}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_local())
