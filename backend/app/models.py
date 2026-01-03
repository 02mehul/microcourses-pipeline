from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    checksum = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="PENDING")  # PENDING/RUNNING/...
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_markdown = Column(Text, nullable=True)  # Parsed markdown from LlamaParse

    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    document = relationship("Document", back_populates="pages")
    blocks = relationship("Block", back_populates="page", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    type = Column(String, default="text")  # text/table/figure
    bbox = Column(JSON, nullable=False)    # {x0,y0,x1,y1} normalized 0-1
    text_raw = Column(String, nullable=True)
    ocr_used = Column(Boolean, default=False)

    page = relationship("Page", back_populates="blocks")
    parent = relationship("Block", remote_side=[id], backref="children")

    # Semantic classification
    semantic_role = Column(String, nullable=True)  # title, chapter_heading, paragraph, etc.
    hierarchy_level = Column(Integer, nullable=True)  # 0=chapter, 1=section, etc.

    # Relationships
    parent_block_id = Column(Integer, ForeignKey("blocks.id"), nullable=True)
    sequence_order = Column(Integer, nullable=True)

    # Rich content
    table_data = Column(JSON, nullable=True)
    table_headers = Column(JSON, nullable=True)
    image_path = Column(String, nullable=True)


    @property
    def page_number(self) -> int:
        """Convenience property to get page number for API responses."""
        return self.page.page_number if self.page else 0


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    slide_number = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    subheading = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    content_chunk = Column(String, nullable=True)  # The raw text chunk used for this slide

    # Hierarchical context (Milestone 3 requirement)
    chapter_title = Column(String, nullable=True)
    subchapter_title = Column(String, nullable=True)
    subchapter_id = Column(String, nullable=True)  # Unique identifier for grouping

    # Table support for visual data presentation
    table_data = Column(JSON, nullable=True)  # {headers: [], rows: [[]], caption: ""}
    has_table = Column(Boolean, default=False)  # Quick flag for frontend layout decisions

    document = relationship("Document", back_populates="slides")
    questions = relationship("Question", back_populates="slide", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    slide_id = Column(Integer, ForeignKey("slides.id"), nullable=True)
    question_text = Column(String, nullable=False)
    answer_text = Column(String, nullable=True)

    # Subchapter grouping (Milestone 3: 3-4 questions per subchapter)
    subchapter_id = Column(String, nullable=True)
    subchapter_title = Column(String, nullable=True)

    document = relationship("Document", back_populates="questions")
    slide = relationship("Slide", back_populates="questions")

# Update Document relationship
Document.slides = relationship("Slide", back_populates="document", cascade="all, delete-orphan")
Document.questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
