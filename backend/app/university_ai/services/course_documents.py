from pathlib import Path
import re
import uuid

from app.university_ai.services.ai_marking import (
    ALLOWED_EXTENSIONS,
    extract_document_text,
)


BASE_STORAGE_DIR = Path("storage") / "university" / "course_documents"


def save_course_document_file(
    file_bytes: bytes,
    filename: str,
    university_id: int,
    course_offering_id: int,
) -> Path:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Supported formats: "
            "PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, WEBP, HEIC and HEIF."
        )

    course_dir = (
        BASE_STORAGE_DIR
        / str(university_id)
        / str(course_offering_id)
    )

    course_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename,
    )

    destination = (
        course_dir
        / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    )

    destination.write_bytes(file_bytes)

    return destination


def extract_course_document_text(file_path: Path) -> str:
    extracted = extract_document_text(file_path)

    if isinstance(extracted, dict):
        return (extracted.get("text") or "").strip()

    return str(extracted or "").strip()