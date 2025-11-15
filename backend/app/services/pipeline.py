"""
PDF processing pipeline using PyMuPDF for text extraction.

This module handles the core document processing workflow:
1. Download PDF from MinIO storage
2. Extract text blocks with bounding box coordinates
3. Normalize coordinates to 0-1 range (resolution-independent)
4. Store structured data in PostgreSQL
"""

import logging
import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from .storage import download_bytes
from ..models import Document, Page, Block

logger = logging.getLogger(__name__)


def process_document(db: Session, document_id: int) -> None:
    """
    Extract text blocks from uploaded PDF using PyMuPDF.

    Process:
    1. Download PDF from MinIO storage
    2. Iterate through pages
    3. Extract text blocks with bounding boxes
    4. Normalize coordinates to 0-1 range (for layout preservation)
    5. Store in PostgreSQL (Document → Page → Block hierarchy)

    Args:
        db: SQLAlchemy database session
        document_id: ID of document to process

    Side Effects:
        - Updates document.status in database (PENDING → RUNNING → SUCCESS/FAILED)
        - Creates Page and Block records
        - Commits changes to database
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    try:
        # Set status to RUNNING
        document.status = "RUNNING"
        db.commit()

        # Download PDF from MinIO
        logger.info(f"Processing document {document_id}: {document.filename}")
        pdf_bytes = download_bytes(document.storage_path)

        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        logger.info(f"PDF has {len(pdf_doc)} pages")

        # Process each page
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            width, height = page.rect.width, page.rect.height

            # Create Page record
            db_page = Page(
                document_id=document_id,
                page_number=page_num + 1,
                width=width,
                height=height,
            )
            db.add(db_page)
            db.flush()  # Get page ID

            # Extract text blocks
            # get_text("blocks") returns: (x0, y0, x1, y1, text, block_type, block_no)
            blocks = page.get_text("blocks")
            logger.info(f"Page {page_num + 1}: extracted {len(blocks)} blocks")

            for block in blocks:
                x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]

                # Skip empty blocks
                if not text or not text.strip():
                    continue

                # Normalize coordinates to 0-1 range
                # This makes coordinates resolution-independent
                # Formula: normalized = pixel_value / page_dimension
                bbox = {
                    "x0": x0 / width,
                    "y0": y0 / height,
                    "x1": x1 / width,
                    "y1": y1 / height,
                }

                db_block = Block(
                    page_id=db_page.id,
                    type="text",
                    bbox=bbox,
                    text_raw=text.strip(),
                    ocr_used=False,
                )
                db.add(db_block)

            db.commit()

        pdf_doc.close()

        # Set status to SUCCESS
        document.status = "SUCCESS"
        db.commit()
        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        document.status = "FAILED"
        db.commit()
        raise  # Re-raise for debugging
