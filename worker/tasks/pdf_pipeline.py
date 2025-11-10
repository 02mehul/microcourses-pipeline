import os
import io
import fitz  # PyMuPDF
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from worker import celery_app
from backend.app.models import Document, Page, Block  # adjust import path as needed
from backend.app.config import Settings

settings = Settings()

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
)

@celery_app.task(name="worker.process_document")
def process_document(document_id: int):
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return

        doc.status = "RUNNING"
        db.commit()

        # download PDF from MinIO
        buf = io.BytesIO()
        s3.download_fileobj(settings.MINIO_BUCKET, doc.storage_path, buf)
        buf.seek(0)

        pdf = fitz.open(stream=buf, filetype="pdf")

        for page_index in range(len(pdf)):
            page = pdf[page_index]
            width, height = page.rect.width, page.rect.height

            page_row = Page(
                document_id=document_id,
                page_number=page_index + 1,
                width=width,
                height=height,
            )
            db.add(page_row)
            db.flush()

            blocks = page.get_text("blocks")  # [x0, y0, x1, y1, text, block_no, ...]
            for (x0, y0, x1, y1, text, *_rest) in blocks:
                if not text.strip():
                    continue
                bbox_norm = {
                    "x0": x0 / width,
                    "y0": y0 / height,
                    "x1": x1 / width,
                    "y1": y1 / height,
                }
                b = Block(
                    page_id=page_row.id,
                    type="text",
                    bbox=bbox_norm,
                    text_raw=text.strip(),
                    ocr_used=False,
                )
                db.add(b)

        doc.status = "SUCCESS"
        db.commit()

    except Exception as e:
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "FAILED"
            # Optional: store error in separate column
            db.commit()
        raise
    finally:
        db.close()
