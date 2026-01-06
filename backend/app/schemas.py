"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data returned by API endpoints,
ensuring type safety and automatic OpenAPI documentation generation.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class BboxSchema(BaseModel):
    """
    Bounding box coordinates in normalized 0-1 range.

    Normalized coordinates are resolution-independent and can be scaled
    to any output format (PowerPoint, HTML, etc.).
    """
    x0: float
    y0: float
    x1: float
    y1: float


class BlockResponse(BaseModel):
    """
    Text block extracted from a PDF page.

    Each block represents a contiguous text region with its position
    preserved via bounding box coordinates.
    """
    id: int
    page_id: int
    page_number: int  # For convenience in frontend (denormalized)
    type: str
    bbox: BboxSchema
    text_raw: str
    ocr_used: bool

    class Config:
        from_attributes = True  # Pydantic v2: allows ORM model conversion


class PageResponse(BaseModel):
    """
    Single page from a PDF document.

    Contains page dimensions and all text blocks extracted from this page.
    """
    id: int
    page_number: int
    width: float
    height: float
    blocks: List[BlockResponse] = []

    class Config:
        from_attributes = True


class DocumentCreateResponse(BaseModel):
    """
    Response after uploading a new document.

    Returns minimal info needed to check processing status or view results.
    """
    document_id: int
    status: str
    status_message: Optional[str] = None
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """
    Review question generated from content.
    """
    id: int
    question_text: str
    answer_text: Optional[str] = None
    subchapter_id: Optional[str] = None
    subchapter_title: Optional[str] = None

    class Config:
        from_attributes = True


class SlideResponse(BaseModel):
    """
    Generated slide content.
    """
    id: int
    slide_number: int
    title: Optional[str] = None
    subheading: Optional[str] = None
    summary: Optional[str] = None
    content_chunk: Optional[str] = None
    chapter_title: Optional[str] = None
    subchapter_title: Optional[str] = None
    subchapter_id: Optional[str] = None
    table_data: Optional[Dict[str, Any]] = None
    has_table: Optional[bool] = False
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


class SlideUpdate(BaseModel):
    """
    Schema for updating slide content.
    """
    title: Optional[str] = None
    subheading: Optional[str] = None
    summary: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []  # List of {"role": "user"|"model", "content": "..."}


class ChatResponse(BaseModel):
    response: str



class RawMarkdownUpdate(BaseModel):
    """Schema for updating raw markdown content."""
    raw_markdown: str


class DocumentDetailResponse(BaseModel):
    """
    Complete document details with all extracted content.

    Includes full hierarchy: Document -> Pages -> Blocks
    """
    id: int
    filename: str
    storage_path: str
    checksum: str
    status: str
    status_message: Optional[str] = None
    created_at: datetime
    raw_markdown: Optional[str] = None
    pages: List[PageResponse] = []
    slides: List[SlideResponse] = []
    questions: List[QuestionResponse] = []
    summary: Optional["DocumentSummaryResponse"] = None

    class Config:
        from_attributes = True


class DocumentStatsSchema(BaseModel):
    """Document statistics for visual display."""
    word_count: int
    reading_time_minutes: int
    page_count: int
    complexity_score: float  # 1-10 scale
    block_count: int
    table_count: int
    image_count: int


class KeyConceptSchema(BaseModel):
    """Key concept extracted from document for chart visualization."""
    name: str
    importance: float  # 0-100 scale
    frequency: int
    category: Optional[str] = None


class TopicDistributionSchema(BaseModel):
    """Topic distribution data for pie/area charts."""
    section: str
    topic: str
    weight: float


class DocumentSummaryResponse(BaseModel):
    """Complete document summary with all visual data."""
    id: int
    document_id: int
    executive_summary: Optional[str] = None
    stats: Optional[DocumentStatsSchema] = None
    key_concepts: List[KeyConceptSchema] = []
    topic_distribution: List[TopicDistributionSchema] = []
    main_takeaways: List[str] = []
    learning_objectives: List[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    """
    detail: str
