"""
PDF processing pipeline using LlamaParse for text extraction and structure analysis.

This module handles the core document processing workflow:
1. Download PDF from MinIO storage
2. Send to LlamaParse Cloud for extraction (Markdown + Images)
3. Parse Markdown to identify semantic structure (Chapters, Sections)
4. Store structured data in PostgreSQL with hierarchy
"""

import logging
import os
import tempfile
import asyncio
from sqlalchemy.orm import Session

import io
from .storage import download_bytes, upload_fileobj
from ..models import Document, Page, Block
from .llamaparse import LlamaParseService
from .markdown_parser import MarkdownParser

from ..db import SessionLocal

logger = logging.getLogger(__name__)


async def process_document(document_id: int) -> None:
    """
    Extract structured content from uploaded PDF using LlamaParse.

    Process:
    1. Download PDF from MinIO
    2. Upload to LlamaParse -> Get Markdown (per page)
    3. Parse Markdown -> Get Blocks with semantic roles
    4. Reconstruct hierarchy (Parent-Child relationships)
    5. Store in DB
    """
    with SessionLocal() as db:
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

            # Create temp file for LlamaParse
            # Determine extension from filename or storage path
            ext = ".pdf"
            if document.filename.lower().endswith(".docx"):
                ext = ".docx"
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name

            try:
                # Call LlamaParse
                logger.info("Sending to LlamaParse...")
                llama_service = LlamaParseService()
                # Returns List[Document] where each doc is a page

                parsed_pages = await llama_service.parse_pdf(temp_file_path)
                logger.info(f"LlamaParse returned {len(parsed_pages)} pages")

                if not parsed_pages:
                    raise Exception("LlamaParse returned no pages. Check API key or file content.")
                

                # Initialize parsers
                md_parser = MarkdownParser()


                # Merge all pages into one text stream to avoid page break issues
                full_text = "\n\n".join([p.text for p in parsed_pages])
                
                # Create a single Page record for the whole document
                # We'll call it Page 1
                logger.info("Processing merged document as Page 1")
                
                db_page = Page(
                    document_id=document_id,
                    page_number=1,
                    width=0, 
                    height=0,
                )
                db.add(db_page)
                db.flush()
                
                # Parse the full merged markdown
                blocks = md_parser.parse(full_text, 1)
                
                for block_data in blocks:
                    # Create Block record
                    db_block = Block(
                        page_id=db_page.id,
                        type=block_data["type"],
                        semantic_role=block_data["semantic_role"],
                        text_raw=block_data["text_raw"],
                        bbox=block_data["bbox"],
                        parent_block_id=None,
                        table_data=block_data.get("table_data"),
                    )
                    db.add(db_block)

                db.commit()

            finally:
                # Cleanup temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # Set status to SUCCESS
            document.status = "SUCCESS"
            db.commit()
            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            document.status = "FAILED"
            db.commit()
