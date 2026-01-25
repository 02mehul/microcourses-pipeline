import logging
import os
import tempfile
from sqlalchemy.orm import Session

import io
from .storage import download_bytes, upload_fileobj
from ..models import Document, Page, Block, DocumentSummary
from .llamaparse import LlamaParseService
from .markdown_parser import MarkdownParser
from .summary_generator import SummaryGenerator

from ..db import SessionLocal

logger = logging.getLogger(__name__)


def process_document(document_id: int) -> None:
    with SessionLocal() as db:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        try:
            document.status = "RUNNING"
            document.status_message = "Extracting content from document..."
            db.commit()

            logger.info(f"📄 Processing document {document_id}: {document.filename}")
            pdf_bytes = download_bytes(document.storage_path)

            ext = ".pdf"
            if document.filename.lower().endswith(".docx"):
                ext = ".docx"
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name

            try:
                logger.info("🚀 Sending for parsing...")
                llama_service = LlamaParseService()

                parsed_pages = llama_service.parse_pdf(temp_file_path)
                logger.info(f"✅ LlamaParse returned {len(parsed_pages)} pages")

                if not parsed_pages:
                    raise Exception("LlamaParse returned no pages. Check API key or file content.")

                full_text = "\n\n".join([p.text for p in parsed_pages])

                document.raw_markdown = full_text
                db.flush()

                docs_dir = os.path.join(os.path.dirname(__file__), "../..", "docs")
                os.makedirs(docs_dir, exist_ok=True)

                doc_base_name = os.path.splitext(document.filename)[0]
                markdown_path = os.path.join(docs_dir, f"{doc_base_name}_{document_id}_parsed.md")

                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                logger.info(f"💾 Saved markdown to: {markdown_path}")

                md_parser = MarkdownParser()
                
                logger.info("🔄 Processing merged document as Page 1")
                
                db_page = Page(
                    document_id=document_id,
                    page_number=1,
                    width=0, 
                    height=0,
                )
                db.add(db_page)
                db.flush()
                
                blocks = md_parser.parse(full_text, 1)
                
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

                logger.info("🎬 Starting content processing (Batch Slide Generation)...")
                document.status_message = "Generating slides from content..."
                db.commit()

                from .content_processor import ContentProcessor
                from ..models import Slide, Question

                processor = ContentProcessor()

                logger.info("🤖 Generating all slides in single batch API call...")
                all_slides = processor.generate_all_slides_batch(db_blocks)
                
                if not all_slides:
                    logger.error("Batch slide generation returned no slides")
                    raise Exception("Failed to generate slides from document content")
                
                logger.info(f"✨ Successfully generated {len(all_slides)} slides in single API call")

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
                        visualization_data=slide_data.get("visualization_data"),
                        table_data=slide_data.get("table_data"),
                        has_table=slide_data.get("has_table", False)
                    )
                    db.add(db_slide)
                    db.flush()
                    db_slides.append(db_slide)

                    viz_data = slide_data.get("visualization_data")
                    if viz_data:
                        if viz_data.get("type") == "chart":
                            viz_info = f" (with {viz_data.get('chart_type')} chart)"
                        elif viz_data.get("type") == "table":
                            viz_info = " (with table)"
                        else:
                            viz_info = " (with visualization)"
                    else:
                        viz_info = ""
                    logger.info(f"Saved slide {i+1}: {slide_data.get('title')}{viz_info}")

                logger.info("❓ Generating review questions per subchapter...")
                document.status_message = "Creating review questions..."
                db.commit()

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
                        logger.info(f"Skipping subchapter '{subchapter.get('subchapter_title')}' - too little content")
                        continue
                    
                    questions_data = processor.generate_questions_for_subchapter(subchapter_content)
                    
                    if not questions_data:
                        logger.warning(f"No questions generated for subchapter: {subchapter.get('subchapter_title')}")
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
                        question_type = q_data.get("question_type", "sentence")
                        db_question = Question(
                            document_id=document_id,
                            slide_id=target_slide.id if target_slide else None,
                            question_text=q_data.get("question_text"),
                            answer_text=q_data.get("answer_text"),
                            subchapter_id=subchapter_id,
                            subchapter_title=subchapter_title,
                            question_type=question_type,
                            options=q_data.get("options"),
                            correct_answer=q_data.get("correct_answer")
                        )
                        db.add(db_question)
                        total_questions += 1

                    type_counts = {}
                    for q_data in questions_data:
                        qtype = q_data.get("question_type", "sentence")
                        type_counts[qtype] = type_counts.get(qtype, 0) + 1
                    type_summary = ", ".join([f"{count} {qtype}" for qtype, count in type_counts.items()])
                    logger.info(f"Generated {len(questions_data)} questions for subchapter '{subchapter_title}': {type_summary}")
                
                logger.info(f"✅ Total questions generated: {total_questions} across {len(subchapters)} subchapters")

                logger.info("📊 Generating document summary...")
                document.status_message = "Building summary and insights..."
                db.commit()

                try:
                    summary_generator = SummaryGenerator()
                    page_count = len(parsed_pages) if parsed_pages else 1
                    summary_data = summary_generator.create_full_summary(db_blocks, page_count)
                    
                    existing_summary = db.query(DocumentSummary).filter(
                        DocumentSummary.document_id == document_id
                    ).first()
                    
                    if existing_summary:
                        existing_summary.executive_summary = summary_data["executive_summary"]
                        existing_summary.stats = summary_data["stats"]
                        existing_summary.key_concepts = summary_data["key_concepts"]
                        existing_summary.topic_distribution = summary_data["topic_distribution"]
                        existing_summary.main_takeaways = summary_data["main_takeaways"]
                        existing_summary.learning_objectives = summary_data["learning_objectives"]
                    else:
                        db_summary = DocumentSummary(
                            document_id=document_id,
                            executive_summary=summary_data["executive_summary"],
                            stats=summary_data["stats"],
                            key_concepts=summary_data["key_concepts"],
                            topic_distribution=summary_data["topic_distribution"],
                            main_takeaways=summary_data["main_takeaways"],
                            learning_objectives=summary_data["learning_objectives"]
                        )
                        db.add(db_summary)
                    
                    logger.info("✅ Document summary generated successfully")
                except Exception as summary_error:
                    logger.warning(f"⚠️ Summary generation failed (non-critical): {summary_error}")

                db.commit()

            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            document.status = "SUCCESS"
            document.status_message = None
            db.commit()
            logger.info(f"🎉 Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            document.status = "FAILED"
            document.status_message = f"Error: {str(e)[:100]}"
            db.commit()


def reprocess_document_from_markdown(document_id: int, new_markdown: str) -> None:
    from .content_processor import ContentProcessor
    from ..models import Slide, Question
    
    with SessionLocal() as db:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for reprocessing")
            return

        try:
            document.status = "RUNNING"
            document.raw_markdown = new_markdown
            db.commit()

            logger.info(f"🔄 Reprocessing document {document_id}: {document.filename}")

            logger.info("🗑️ Clearing existing pages, blocks, slides, and questions...")
            db.query(Question).filter(Question.document_id == document_id).delete()
            db.query(Slide).filter(Slide.document_id == document_id).delete()
            
            for page in document.pages:
                db.delete(page)
            db.flush()

            md_parser = MarkdownParser()
            
            logger.info("🔄 Processing edited markdown as Page 1")
            
            db_page = Page(
                document_id=document_id,
                page_number=1,
                width=0, 
                height=0,
            )
            db.add(db_page)
            db.flush()
            
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

            logger.info("🎬 Starting content processing (Batch Slide Generation)...")
            processor = ContentProcessor()

            logger.info("🤖 Generating all slides in single batch API call...")
            all_slides = processor.generate_all_slides_batch(db_blocks)
            
            if not all_slides:
                logger.error("Batch slide generation returned no slides")
                raise Exception("Failed to generate slides from document content")
            
            logger.info(f"✨ Successfully generated {len(all_slides)} slides")

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

            logger.info("📊 Generating document summary...")
            try:
                summary_generator = SummaryGenerator()
                page_count = 1
                summary_data = summary_generator.create_full_summary(db_blocks, page_count)
                
                db.query(DocumentSummary).filter(
                    DocumentSummary.document_id == document_id
                ).delete()
                
                db_summary = DocumentSummary(
                    document_id=document_id,
                    executive_summary=summary_data["executive_summary"],
                    stats=summary_data["stats"],
                    key_concepts=summary_data["key_concepts"],
                    topic_distribution=summary_data["topic_distribution"],
                    main_takeaways=summary_data["main_takeaways"],
                    learning_objectives=summary_data["learning_objectives"]
                )
                db.add(db_summary)
                
                logger.info("✅ Document summary generated successfully")
            except Exception as summary_error:
                logger.warning(f"⚠️ Summary generation failed (non-critical): {summary_error}")

            db.commit()

            document.status = "SUCCESS"
            db.commit()
            logger.info(f"🎉 Document {document_id} reprocessed successfully")

        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {str(e)}", exc_info=True)
            document.status = "FAILED"
            db.commit()
