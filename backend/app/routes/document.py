import hashlib
import io
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..db import SessionLocal
from .. import models
from .. import schemas
from ..services import storage
from ..services.pipeline import process_document, reprocess_document_from_markdown

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put("/slides/{slide_id}", response_model=schemas.SlideResponse)
def update_slide(slide_id: int, slide_update: schemas.SlideUpdate, db: Session = Depends(get_db)):
    slide = db.query(models.Slide).filter(models.Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    if slide_update.title is not None:
        slide.title = slide_update.title
    if slide_update.subheading is not None:
        slide.subheading = slide_update.subheading
    if slide_update.summary is not None:
        slide.summary = slide_update.summary

    db.commit()
    db.refresh(slide)
    return slide



@router.get("/", response_model=List[schemas.DocumentCreateResponse])
def list_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, SUCCESS, FAILED)"),
    db: Session = Depends(get_db),
):
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
        schemas.DocumentCreateResponse(
            document_id=doc.id,
            status=doc.status,
            filename=doc.filename,
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@router.post("/", response_model=schemas.DocumentCreateResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    allowed_extensions = {".pdf", ".docx"}
    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    checksum = hashlib.md5(data).hexdigest()
    key = f"documents/{checksum}_{file.filename}"

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

    background_tasks.add_task(process_document, doc.id)

    db.refresh(doc)

    return schemas.DocumentCreateResponse(
        document_id=doc.id,
        status=doc.status,
        filename=doc.filename,
        created_at=doc.created_at
    )


@router.get("/{document_id}", response_model=schemas.DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    doc = (
        db.query(models.Document)
        .options(
            joinedload(models.Document.slides),
            joinedload(models.Document.questions),
            joinedload(models.Document.summary)
        )
        .filter(models.Document.id == document_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/summary", response_model=schemas.DocumentSummaryResponse)
def get_document_summary(document_id: int, db: Session = Depends(get_db)):
    summary = db.query(models.DocumentSummary).filter(
        models.DocumentSummary.document_id == document_id
    ).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not generated yet")
    return summary


@router.post("/{document_id}/summary/regenerate")
def regenerate_summary(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from ..services.summary_generator import SummaryGenerator
    from ..models import DocumentSummary, Block, Page
    
    def generate_summary_task(doc_id: int):
        from ..db import SessionLocal
        with SessionLocal() as task_db:
            pages = task_db.query(Page).filter(Page.document_id == doc_id).all()
            all_blocks = []
            for page in pages:
                all_blocks.extend(page.blocks)
            
            if not all_blocks:
                return
            
            try:
                generator = SummaryGenerator()
                summary_data = generator.create_full_summary(all_blocks, len(pages))
                
                task_db.query(DocumentSummary).filter(
                    DocumentSummary.document_id == doc_id
                ).delete()
                
                db_summary = DocumentSummary(
                    document_id=doc_id,
                    executive_summary=summary_data["executive_summary"],
                    stats=summary_data["stats"],
                    key_concepts=summary_data["key_concepts"],
                    topic_distribution=summary_data["topic_distribution"],
                    main_takeaways=summary_data["main_takeaways"],
                    learning_objectives=summary_data["learning_objectives"]
                )
                task_db.add(db_summary)
                task_db.commit()
            except Exception as e:
                import logging
                logging.error(f"Failed to regenerate summary: {e}")
    
    background_tasks.add_task(generate_summary_task, document_id)
    return {"message": "Summary regeneration started"}


@router.get("/{document_id}/raw")
def get_raw_markdown(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"raw_markdown": doc.raw_markdown or ""}


@router.put("/{document_id}/raw")
def update_raw_markdown(
    document_id: int,
    body: schemas.RawMarkdownUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc.status = "RUNNING"
    db.commit()
    
    background_tasks.add_task(reprocess_document_from_markdown, document_id, body.raw_markdown)
    
    return {"message": "Reprocessing started", "status": "RUNNING"}


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
                    "semantic_role": b.semantic_role,
                    "hierarchy_level": b.hierarchy_level,
                    "parent_block_id": b.parent_block_id,
                    "bbox": b.bbox,
                    "text": b.text_raw,
                    "table_data": b.table_data,
                }
            )

    return result


@router.post("/{document_id}/chat", response_model=schemas.ChatResponse)
def chat_document(
    document_id: int,
    chat_request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = db.query(models.Page).filter(models.Page.document_id == document_id).all()
    all_text = []
    for p in pages:
        for b in p.blocks:
            if b.text_raw:
                text_part = b.text_raw
                if b.table_data:
                    import json
                    text_part += f"\n[TABLE_DATA] {json.dumps(b.table_data)}"
                all_text.append(text_part)

    full_text = "\n\n".join(all_text)

    if not full_text:
        raise HTTPException(status_code=400, detail="Document has no text content")

    from ..services.content_processor import ContentProcessor
    processor = ContentProcessor()

    response_text = processor.chat_with_document(
        document_text=full_text,
        message=chat_request.message,
        history=chat_request.history
    )

    return schemas.ChatResponse(response=response_text)


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        storage.delete_file(doc.storage_path)
    except Exception as e:
        import logging
        logging.warning(f"Failed to delete file from storage: {e}")

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully", "document_id": document_id}
