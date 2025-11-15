from sqlalchemy import (
    Column,
    Integer,
    String,
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

    @property
    def page_number(self) -> int:
        """Convenience property to get page number for API responses."""
        return self.page.page_number if self.page else 0
