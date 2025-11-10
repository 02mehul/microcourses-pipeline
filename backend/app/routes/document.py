import hashlib
import io

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal
from .. import models
from ..schemas import DocumentCreateResponse, DocumentDetailResponse
from ..services import storage
from ..services.pipeline import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DocumentCreateResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    checksum = hashlib.md5(data).hexdigest()
    key = f"pdf/{checksum}_{file.filename}"

    storage.upload_fileobj(io.BytesIO(data), key)

    doc = models.Document(
        filename=file.filename,
        storage_path=key,
        checksum=checksum,
        status="PENDING",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Run pipeline (sync for now)
    process_document(db, doc.id)

    return DocumentCreateResponse(document_id=doc.id, status="SUCCESS")


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/blocks")
def get_blocks(document_id: int, db: Session = Depends(get_db)):
    pages = (
        db.query(models.Page)
        .filter(models.Page.document_id == document_id)
        .order_by(models.Page.page_number)
        .all()
    )
    if not pages:
        raise HTTPException(status_code=404, detail="No pages/blocks for this document")

    result = []
    for p in pages:
        for b in p.blocks:
            result.append(
                {
                    "page": p.page_number,
                    "type": b.type,
                    "bbox": b.bbox,
                    "text": b.text_raw,
                }
            )
    return result
