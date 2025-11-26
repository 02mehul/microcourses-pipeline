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
from .json_parser import JsonParser
# from .image_handler import ImageHandler # Removed image handling
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
                # Returns List[Document] where each doc is a page
                parsed_pages = await llama_service.parse_pdf(temp_file_path)
                logger.info(f"LlamaParse returned {len(parsed_pages)} pages")

                if not parsed_pages:
                    raise Exception("LlamaParse returned no pages. Check API key or file content.")
                
                # DEBUG: Save raw output to local docs/ folder for inspection
                try:
                    # Assuming docs/ is in the project root, relative to where this runs
                    # We can try to find the docs folder or just use an absolute path if known, 
                    # but let's try a relative path from the app root.
                    # If running via docker, this might be inside the container.
                    # If running locally via script, it depends on CWD.
                    # Let's try to save to the same 'docs' folder where we look for uploads in dev
                    local_docs_path = os.path.join(os.getcwd(), "docs")
                    if not os.path.exists(local_docs_path):
                        os.makedirs(local_docs_path, exist_ok=True)
                        
                    debug_file_path = os.path.join(local_docs_path, f"raw_output_{document_id}.md")
                    with open(debug_file_path, "w", encoding="utf-8") as f:
                        f.write(full_markdown)
                    logger.info(f"Saved raw LlamaParse output to {debug_file_path}")
                except Exception as e:
                    logger.error(f"Failed to save debug raw output: {e}")
                
                # Initialize parsers
                # image_handler = ImageHandler() # Removed
                md_parser = MarkdownParser()
                # json_parser = JsonParser() # Removed
                
                # Hierarchy tracking state
                # Stack of {"level": int, "block_id": int}
                # hierarchy_stack = []

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
