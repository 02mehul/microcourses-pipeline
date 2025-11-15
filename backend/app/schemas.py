"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data returned by API endpoints,
ensuring type safety and automatic OpenAPI documentation generation.
"""

from pydantic import BaseModel
from typing import List, Optional
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
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


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
    created_at: datetime
    pages: List[PageResponse] = []

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    """
    detail: str
