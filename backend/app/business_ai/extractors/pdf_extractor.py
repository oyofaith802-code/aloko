from pathlib import Path
from typing import Any

from pypdf import PdfReader


def extract_pdf(file_path: str | Path) -> dict[str, Any]:
    """
    Extract text from a PDF document.

    Returns a normalized structure that can later be expanded
    to support tables, OCR, and page-level intelligence.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(str(path))

    pages = []
    full_text_parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = text.strip()

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

        if text:
            full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)

    return {
        "source_type": "pdf",
        "filename": path.name,
        "page_count": len(reader.pages),
        "text": full_text,
        "pages": pages,
    }