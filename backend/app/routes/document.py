import hashlib
import io
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
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


@router.get("/", response_model=List[DocumentCreateResponse])
def list_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, SUCCESS, FAILED)"),
    db: Session = Depends(get_db),
):
    """
    List all documents with optional filtering and pagination.

    Query Parameters:
    - skip: Offset for pagination (default: 0)
    - limit: Maximum results to return (default: 20, max: 100)
    - status: Filter by document status (optional)

    Returns:
        List of documents with basic metadata
    """
    query = db.query(models.Document)

    if status:
        query = query.filter(models.Document.status == status)

    documents = (
        query.order_by(models.Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        DocumentCreateResponse(
            document_id=doc.id,
            status=doc.status,
            filename=doc.filename,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


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

    # Refresh to get updated status and created_at
    db.refresh(doc)

    return DocumentCreateResponse(
        document_id=doc.id,
        status=doc.status,
        filename=doc.filename,
        created_at=doc.created_at
    )


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
