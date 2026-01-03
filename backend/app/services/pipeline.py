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
from sqlalchemy.orm import Session

import io
from .storage import download_bytes, upload_fileobj
from ..models import Document, Page, Block
from .llamaparse import LlamaParseService
from .markdown_parser import MarkdownParser

from ..db import SessionLocal

logger = logging.getLogger(__name__)


def process_document(document_id: int) -> None:
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
            logger.info(f"📄 Processing document {document_id}: {document.filename}")
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
                logger.info("🚀 Sending for parsing...")
                llama_service = LlamaParseService()
                # Returns List[Document] where each doc is a page

                parsed_pages = llama_service.parse_pdf(temp_file_path)
                logger.info(f"✅ LlamaParse returned {len(parsed_pages)} pages")

                if not parsed_pages:
                    raise Exception("LlamaParse returned no pages. Check API key or file content.")


                # Merge all pages into one text stream to avoid page break issues
                full_text = "\n\n".join([p.text for p in parsed_pages])

                # Store raw markdown in database for later editing
                document.raw_markdown = full_text
                db.flush()

                # Save markdown to backend/docs/ for analysis and improvement
                docs_dir = os.path.join(os.path.dirname(__file__), "../..", "docs")
                os.makedirs(docs_dir, exist_ok=True)

                # Generate unique filename using document ID to avoid conflicts
                doc_base_name = os.path.splitext(document.filename)[0]
                markdown_path = os.path.join(docs_dir, f"{doc_base_name}_{document_id}_parsed.md")

                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                logger.info(f"💾 Saved markdown to: {markdown_path}")

                # Initialize parsers
                md_parser = MarkdownParser()
                
                # Create a single Page record for the whole document
                # We'll call it Page 1
                logger.info("🔄 Processing merged document as Page 1")
                
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
                
                db_blocks = []
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
                        hierarchy_level=block_data.get("hierarchy_level"),
                    )
                    db.add(db_block)
                    db_blocks.append(db_block)

                db.flush() # Ensure blocks have IDs and are ready
                logger.info(f"📦 Stored {len(db_blocks)} blocks in database")

                # --- Milestone 3: Content Processing ---
                logger.info("🎬 Starting content processing (Batch Slide Generation)...")
                from .content_processor import ContentProcessor
                from ..models import Slide, Question

                processor = ContentProcessor()  # Uses GEMINI_API_KEY from environment

                # NEW APPROACH: Generate ALL slides in a single batch API call
                # The AI will determine the optimal number of slides (typically 5-10)
                logger.info("🤖 Generating all slides in single batch API call...")
                all_slides = processor.generate_all_slides_batch(db_blocks)
                
                if not all_slides:
                    logger.error("Batch slide generation returned no slides")
                    raise Exception("Failed to generate slides from document content")
                
                logger.info(f"✨ Successfully generated {len(all_slides)} slides in single API call")

                # Save slides to database
                db_slides = []
                for i, slide_data in enumerate(all_slides):
                    db_slide = Slide(
                        document_id=document_id,
                        slide_number=i+1,
                        title=slide_data.get("title"),
                        subheading=slide_data.get("subheading"),
                        summary=slide_data.get("summary"),
                        content_chunk="",  # No chunking needed with batch approach
                        chapter_title="",  # Optional: Can be enhanced later
                        subchapter_title="",
                        subchapter_id=f"slide_{i+1}",
                        table_data=slide_data.get("table_data"),
                        has_table=slide_data.get("has_table", False)
                    )
                    db.add(db_slide)
                    db.flush()  # Get ID
                    db_slides.append(db_slide)

                    # Log with table info
                    table_info = " (with table)" if slide_data.get("has_table") else ""
                    logger.info(f"Saved slide {i+1}: {slide_data.get('title')}{table_info}")

                # Generate Questions for EACH subchapter (Milestone 3: 3-4 questions per subchapter)
                logger.info("❓ Generating review questions per subchapter...")
                
                # Detect subchapters from blocks
                subchapters = processor.detect_subchapters(db_blocks)
                total_questions = 0
                
                for subchapter in subchapters:
                    subchapter_blocks = subchapter.get("blocks", [])
                    if not subchapter_blocks:
                        continue
                    
                    # Combine subchapter content for question generation
                    subchapter_content = "\n\n".join([
                        block.text_raw for block in subchapter_blocks if block.text_raw
                    ])[:8000]  # Limit per subchapter (increased from 4000)
                    
                    if len(subchapter_content.strip()) < 50:
                        logger.info(f"Skipping subchapter '{subchapter.get('subchapter_title')}' - too little content")
                        continue
                    
                    # Generate 3-4 questions for this subchapter
                    questions_data = processor.generate_questions_for_subchapter(subchapter_content)
                    
                    if not questions_data:
                        logger.warning(f"No questions generated for subchapter: {subchapter.get('subchapter_title')}")
                        continue
                    
                    # Find the slide(s) that belong to this subchapter
                    subchapter_id = subchapter.get("id")
                    subchapter_title = subchapter.get("subchapter_title", "")
                    
                    # Distribute questions across slides proportionally
                    # Since batch slides don't have matching subchapter_ids, assign based on position
                    subchapter_index = subchapters.index(subchapter)
                    if db_slides and len(subchapters) > 0:
                        # Map subchapter to slide proportionally
                        slide_index = min(
                            int(subchapter_index * len(db_slides) / len(subchapters)),
                            len(db_slides) - 1
                        )
                        target_slide = db_slides[slide_index]
                    else:
                        target_slide = None
                    
                    for q_data in questions_data:
                        db_question = Question(
                            document_id=document_id,
                            slide_id=target_slide.id if target_slide else None,
                            question_text=q_data.get("question_text"),
                            answer_text=q_data.get("answer_text"),
                            subchapter_id=subchapter_id,
                            subchapter_title=subchapter_title
                        )
                        db.add(db_question)
                        total_questions += 1
                    
                    logger.info(f"Generated {len(questions_data)} questions for subchapter: {subchapter_title}")
                
                logger.info(f"✅ Total questions generated: {total_questions} across {len(subchapters)} subchapters")

                db.commit()

            finally:
                # Cleanup temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # Set status to SUCCESS
            document.status = "SUCCESS"
            db.commit()
            logger.info(f"🎉 Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            document.status = "FAILED"
            db.commit()


def reprocess_document_from_markdown(document_id: int, new_markdown: str) -> None:
    """
    Reprocess a document from edited markdown content.
    
    This clears all existing Pages, Blocks, Slides, Questions and regenerates them
    from the new markdown content.
    """
    from .content_processor import ContentProcessor
    from ..models import Slide, Question
    
    with SessionLocal() as db:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for reprocessing")
            return

        try:
            # Set status to RUNNING
            document.status = "RUNNING"
            document.raw_markdown = new_markdown
            db.commit()

            logger.info(f"🔄 Reprocessing document {document_id}: {document.filename}")

            # Clear existing data
            logger.info("🗑️ Clearing existing pages, blocks, slides, and questions...")
            db.query(Question).filter(Question.document_id == document_id).delete()
            db.query(Slide).filter(Slide.document_id == document_id).delete()
            
            # Clear pages (which cascades to blocks)
            for page in document.pages:
                db.delete(page)
            db.flush()

            # Initialize parsers
            md_parser = MarkdownParser()
            
            # Create a single Page record for the whole document
            logger.info("🔄 Processing edited markdown as Page 1")
            
            db_page = Page(
                document_id=document_id,
                page_number=1,
                width=0, 
                height=0,
            )
            db.add(db_page)
            db.flush()
            
            # Parse the markdown
            blocks = md_parser.parse(new_markdown, 1)
            
            db_blocks = []
            for block_data in blocks:
                db_block = Block(
                    page_id=db_page.id,
                    type=block_data["type"],
                    semantic_role=block_data["semantic_role"],
                    text_raw=block_data["text_raw"],
                    bbox=block_data["bbox"],
                    parent_block_id=None,
                    table_data=block_data.get("table_data"),
                    hierarchy_level=block_data.get("hierarchy_level"),
                )
                db.add(db_block)
                db_blocks.append(db_block)

            db.flush()
            logger.info(f"📦 Stored {len(db_blocks)} blocks in database")

            # Generate slides
            logger.info("🎬 Starting content processing (Batch Slide Generation)...")
            processor = ContentProcessor()

            logger.info("🤖 Generating all slides in single batch API call...")
            all_slides = processor.generate_all_slides_batch(db_blocks)
            
            if not all_slides:
                logger.error("Batch slide generation returned no slides")
                raise Exception("Failed to generate slides from document content")
            
            logger.info(f"✨ Successfully generated {len(all_slides)} slides")

            # Save slides to database
            db_slides = []
            for i, slide_data in enumerate(all_slides):
                db_slide = Slide(
                    document_id=document_id,
                    slide_number=i+1,
                    title=slide_data.get("title"),
                    subheading=slide_data.get("subheading"),
                    summary=slide_data.get("summary"),
                    content_chunk="",
                    chapter_title="",
                    subchapter_title="",
                    subchapter_id=f"slide_{i+1}",
                    table_data=slide_data.get("table_data"),
                    has_table=slide_data.get("has_table", False)
                )
                db.add(db_slide)
                db.flush()
                db_slides.append(db_slide)

            # Generate Questions
            logger.info("❓ Generating review questions per subchapter...")
            
            subchapters = processor.detect_subchapters(db_blocks)
            total_questions = 0
            
            for subchapter in subchapters:
                subchapter_blocks = subchapter.get("blocks", [])
                if not subchapter_blocks:
                    continue
                
                subchapter_content = "\n\n".join([
                    block.text_raw for block in subchapter_blocks if block.text_raw
                ])[:8000]
                
                if len(subchapter_content.strip()) < 50:
                    continue
                
                questions_data = processor.generate_questions_for_subchapter(subchapter_content)
                
                if not questions_data:
                    continue
                
                subchapter_id = subchapter.get("id")
                subchapter_title = subchapter.get("subchapter_title", "")
                
                subchapter_index = subchapters.index(subchapter)
                if db_slides and len(subchapters) > 0:
                    slide_index = min(
                        int(subchapter_index * len(db_slides) / len(subchapters)),
                        len(db_slides) - 1
                    )
                    target_slide = db_slides[slide_index]
                else:
                    target_slide = None
                
                for q_data in questions_data:
                    db_question = Question(
                        document_id=document_id,
                        slide_id=target_slide.id if target_slide else None,
                        question_text=q_data.get("question_text"),
                        answer_text=q_data.get("answer_text"),
                        subchapter_id=subchapter_id,
                        subchapter_title=subchapter_title
                    )
                    db.add(db_question)
                    total_questions += 1
            
            logger.info(f"✅ Total questions generated: {total_questions}")

            db.commit()

            # Set status to SUCCESS
            document.status = "SUCCESS"
            db.commit()
            logger.info(f"🎉 Document {document_id} reprocessed successfully")

        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {str(e)}", exc_info=True)
            document.status = "FAILED"
            db.commit()

