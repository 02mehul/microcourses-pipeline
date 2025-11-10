import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from .storage import download_bytes
from ..models import Document, Page, Block


def process_document(db: Session, document_id: int) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        return

    # mark running
    doc.status = "RUNNING"
    db.commit()

    pdf_data = download_bytes(doc.storage_path)
    pdf = fitz.open(stream=pdf_data, filetype="pdf")

    for page_index in range(len(pdf)):
        page = pdf[page_index]
        width, height = page.rect.width, page.rect.height

        page_row = Page(
            document_id=document_id,
            page_number=page_index + 1,
            width=width,
            height=height,
        )
        db.add(page_row)
        db.flush()  # get page_row.id

        # get_text("blocks") returns: x0, y0, x1, y1, text, block_no, ...
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4]
            if not text or not text.strip():
                continue

            bbox_norm = {
                "x0": x0 / width,
                "y0": y0 / height,
                "x1": x1 / width,
                "y1": y1 / height,
            }

            db.add(
                Block(
                    page_id=page_row.id,
                    type="text",
                    bbox=bbox_norm,
                    text_raw=text.strip(),
                    ocr_used=False,
                )
            )

    doc.status = "SUCCESS"
    db.commit()
