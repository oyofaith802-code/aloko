from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.business_ai.extractors.pdf_extractor import extract_pdf
from app.business_ai.extractors.docx_extractor import extract_docx

from app.university_ai.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentSubmission,
    AIMarkingJob,
    AIMarkingResult,
    Student,
)


# ============================================================
# STORAGE / FILE TYPES
# ============================================================

BASE_STORAGE_DIR = Path("storage") / "university_ai_marking"
BASE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# Aloko should accept normal documents, scans, photographs,
# and common phone-image formats.
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
}

QUESTION_PAPER_EXTENSIONS = ALLOWED_EXTENSIONS.copy()

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
}


# ============================================================
# OPTIONAL IMAGE/OCR SUPPORT
# ============================================================

try:
    from PIL import Image
except ImportError:
    Image = None


try:
    import pytesseract

except ImportError:
    pytesseract = None


# ============================================================
# FILE STORAGE
# ============================================================

def save_marking_file(
    file_bytes: bytes,
    filename: str,
    university_id: int,
    assessment_id: int,
) -> Path:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Supported formats: "
            "PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, WEBP, HEIC and HEIF."
        )

    assessment_dir = (
        BASE_STORAGE_DIR
        / str(university_id)
        / str(assessment_id)
    )

    assessment_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename,
    )

    destination = (
        assessment_dir
        / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    )

    destination.write_bytes(file_bytes)

    return destination


# ============================================================
# STUDENT / MATRIC HELPERS
# ============================================================

def extract_matric_number(
    filename: str,
) -> Optional[str]:
    """
    Extract matric number from the beginning of a filename.

    Examples:

        2024-001_answer.pdf
        2024-001_answer.docx
        MAT123_answer.pdf
        MAT123.pdf
        CSC-2026-001.jpg
    """

    stem = Path(filename).stem.strip()

    if not stem:
        return None

    match = re.match(
        r"^([A-Za-z0-9/_.-]+?)(?:[_-]|$)",
        stem,
    )

    if not match:
        return None

    return match.group(1).strip() or None


def find_student_by_matric(
    db: Session,
    university_id: int,
    matric_number: str,
) -> Optional[Student]:

    return (
        db.query(Student)
        .filter(
            Student.university_id == university_id,
            Student.matric_number == matric_number,
            Student.status == "active",
        )
        .first()
    )


def verify_student_enrollment(
    db: Session,
    student_id: int,
    course_offering_id: int,
) -> bool:

    from app.university_ai.models import StudentCourse

    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.student_id == student_id,
            StudentCourse.course_offering_id == course_offering_id,
        )
        .first()
    )

    return enrollment is not None


# ============================================================
# IMAGE OCR
# ============================================================

def extract_image_text(
    file_path: Path,
) -> str:
    """
    Extract text from a photographed or scanned paper.

    This provides a basic OCR layer.

    IMPORTANT:
    Tesseract is useful for printed/scanned text, but it is
    not reliable enough to be treated as the final solution
    for difficult handwriting.

    A vision-capable AI extraction layer can be added later
    without changing the rest of the marking pipeline.
    """

    if Image is None:
        raise ValueError(
            "Pillow is required to process image papers. "
            "Install it with: pip install pillow"
        )

    if pytesseract is None:
        raise ValueError(
            "pytesseract is required to process image papers. "
            "Install it with: pip install pytesseract"
        )

    try:
        tesseract_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(tesseract_exe).exists():
            pytesseract.pytesseract.tesseract_cmd = tesseract_exe

        image = Image.open(file_path)

        # Convert images into OCR-friendly modes.
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )

        return text.strip()

    except Exception as exc:
        raise ValueError(
            f"Could not extract text from image: {exc}"
        )


# ============================================================
# UNIVERSAL DOCUMENT EXTRACTION
# ============================================================

def extract_document_text(
    file_path: Path,
) -> str:
    """
    Universal extraction layer.

    Supported:

        PDF
        DOCX
        TXT
        JPG
        JPEG
        PNG
        WEBP
        HEIC
        HEIF

    Legacy .DOC is accepted by the upload layer but requires
    conversion before text extraction.
    """

    extension = file_path.suffix.lower()

    # ----------------------------------------
    # PDF
    # ----------------------------------------

    if extension == ".pdf":
        result = extract_pdf(file_path)

        if isinstance(result, dict):
            return str(result.get("text", "") or "").strip()

        return str(result or "").strip()

    # ----------------------------------------
    # DOCX
    # ----------------------------------------

    if extension == ".docx":
        result = extract_docx(file_path)

        if isinstance(result, dict):
            return str(result.get("text", "") or "").strip()

        return str(result or "").strip()

    # ----------------------------------------
    # TXT
    # ----------------------------------------

    if extension == ".txt":
        return file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).strip()

    # ----------------------------------------
    # IMAGE
    # ----------------------------------------

    if extension in IMAGE_EXTENSIONS:
        return extract_image_text(file_path)

    # ----------------------------------------
    # LEGACY DOC
    # ----------------------------------------

    if extension == ".doc":
        raise ValueError(
            "Legacy .doc files are accepted for upload but "
            "require document conversion before extraction. "
            "Please use .docx, PDF, or an image for immediate processing."
        )

    raise ValueError(
        f"Unsupported document format: {extension}"
    )


def extract_question_paper(
    file_path: Path,
) -> dict:
    """
    Extract a question paper from any supported document/image.
    """

    text = extract_document_text(file_path)

    extension = file_path.suffix.lower()

    source = (
        "image_ocr"
        if extension in IMAGE_EXTENSIONS
        else "document_extraction"
    )

    return {
        "text": text,
        "file_type": extension,
        "source": source,
    }


def extract_submission_text(
    file_path: Path,
) -> str:
    """
    Extract a student's answer paper from any supported format.
    """

    return extract_document_text(file_path)


# ============================================================
# QUESTION PAPER PARSING
# ============================================================

def parse_questions(
    text: str,
) -> list[dict]:
    """
    Detect numbered questions and their marks.

    Supported examples:

        1. Explain photosynthesis. (10 marks)

        2. Define an algorithm. [5 marks]

        Question 3: Explain recursion. 10 marks

        Q4. What is Python? (5)

    """

    if not text or not text.strip():
        return []

    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    # Keep line structure because question numbers often
    # appear at the beginning of lines.
    normalized = re.sub(
        r"[ \t]+",
        " ",
        normalized,
    )

    pattern = re.compile(
        r"(?im)"
        r"^\s*"
        r"(?:question\s*|q\s*)?"
        r"(\d+)"
        r"\s*"
        r"(?:[.):\-]|\s)"
        r"\s*"
    )

    matches = list(
        pattern.finditer(normalized)
    )

    questions = []

    for index, match in enumerate(matches):

        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(normalized)
        )

        question_text = normalized[
            start:end
        ].strip()

        if not question_text:
            continue

        # ----------------------------------------
        # Detect marks
        # ----------------------------------------

        mark_match = re.search(
            r"""
            (?:
                \(\s*(\d+(?:\.\d+)?)\s*marks?\s*\)
                |
                \[\s*(\d+(?:\.\d+)?)\s*marks?\s*\]
                |
                \b(\d+(?:\.\d+)?)\s*marks?\b
            )
            """,
            question_text,
            re.IGNORECASE | re.VERBOSE,
        )

        max_score = None

        if mark_match:
            for group in mark_match.groups():
                if group is not None:
                    max_score = float(group)
                    break

        # ----------------------------------------
        # Remove marks from question text
        # ----------------------------------------

        cleaned = re.sub(
            r"""
            \(\s*\d+(?:\.\d+)?\s*marks?\s*\)
            |
            \[\s*\d+(?:\.\d+)?\s*marks?\s*\]
            |
            \b\d+(?:\.\d+)?\s*marks?\b
            """,
            "",
            question_text,
            flags=re.IGNORECASE | re.VERBOSE,
        ).strip()

        questions.append(
            {
                "question_number": match.group(1),
                "question_text": cleaned,
                "max_score": max_score,
            }
        )

    return questions


# ============================================================
# STUDENT ANSWER SEGMENTATION
# ============================================================

def extract_student_answers(
    text: str,
) -> dict[str, str]:
    """
    Split ONE student's answer paper into separate answers.

    Supported formats:

        1. Answer...

        2. Answer...

        1) Answer...

        1: Answer...

        Q1. Answer...

        Q2 Answer...

        Question 1: Answer...

    Returns:

        {
            "1": "Answer to question 1",
            "2": "Answer to question 2",
        }

    IMPORTANT:

    This function works on ONE student's submission only.
    It never combines answers from different students.
    """

    if not text or not text.strip():
        return {}

    normalized = (
        text.replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    normalized = re.sub(
        r"[ \t]+",
        " ",
        normalized,
    )

    pattern = re.compile(
        r"(?im)"
        r"^\s*"
        r"(?:"
        r"question\s*"
        r"|q\s*"
        r")?"
        r"(\d+)"
        r"\s*"
        r"(?:[.):\-]|\s)"
        r"\s*"
    )

    matches = list(
        pattern.finditer(normalized)
    )

    if not matches:
        return {}

    answers: dict[str, str] = {}

    for index, match in enumerate(matches):

        question_number = (
            match.group(1).strip()
        )

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(normalized)

        answer = normalized[
            start:end
        ].strip()

        if not answer:
            continue

        if question_number in answers:
            answers[question_number] = (
                answers[question_number]
                + "\n\n"
                + answer
            )
        else:
            answers[question_number] = answer

    return answers


def extract_answer_for_question(
    submission_text: str,
    question_number: str,
) -> Optional[str]:
    """
    Return ONLY the answer belonging to one question.
    """

    question_number = str(
        question_number
    ).strip()

    if not question_number:
        return None

    answers = extract_student_answers(
        submission_text
    )

    return answers.get(
        question_number
    )


# ============================================================
# DATABASE CREATION HELPERS
# ============================================================

def create_question(
    db: Session,
    university_id: int,
    assessment_id: int,
    question_number: str,
    question_text: str,
    max_score: float,
    created_by: int,
    model_answer: Optional[str] = None,
    marking_scheme: Optional[str] = None,
) -> AssessmentQuestion:

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == university_id,
        )
        .first()
    )

    if not assessment:
        raise ValueError(
            "Assessment not found."
        )

    if max_score <= 0:
        raise ValueError(
            "Question maximum score must be greater than zero."
        )

    question = AssessmentQuestion(
        university_id=university_id,
        assessment_id=assessment_id,
        question_number=question_number,
        question_text=question_text,
        max_score=max_score,
        model_answer=model_answer,
        marking_scheme=marking_scheme,
        created_by=created_by,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


def create_submission(
    db: Session,
    university_id: int,
    assessment_id: int,
    student_id: int,
    file_name: str,
    file_path: str,
    extracted_text: Optional[str] = None,
) -> AssessmentSubmission:

    submission = AssessmentSubmission(
        university_id=university_id,
        assessment_id=assessment_id,
        student_id=student_id,
        file_name=file_name,
        file_path=file_path,
        extracted_text=extracted_text,
        status="uploaded",
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission


def create_marking_job(
    db: Session,
    university_id: int,
    assessment_id: int,
    created_by: int,
    submission_ids: list[int],
) -> AIMarkingJob:

    submission_ids = list(
        dict.fromkeys(
            int(submission_id)
            for submission_id in submission_ids
        )
    )

    job = AIMarkingJob(
        university_id=university_id,
        assessment_id=assessment_id,
        created_by=created_by,
        status="processing",
        total_submissions=len(submission_ids),
        processed_submissions=0,
        submission_ids=json.dumps(submission_ids),
        ai_provider="ollama",
        ai_model="llama3.2",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def create_marking_result(
    db: Session,
    university_id: int,
    job_id: int,
    submission_id: int,
    question_id: int,
    student_id: int,
    extracted_answer: Optional[str],
    suggested_score: Optional[float],
    max_score: float,
    confidence: Optional[float],
    grading_evidence: Optional[str],
    feedback: Optional[str],
    ai_provider: Optional[str] = "ollama",
    ai_model: Optional[str] = "llama3.2",
) -> AIMarkingResult:

    if suggested_score is not None:
        suggested_score = max(
            0.0,
            min(
                float(suggested_score),
                float(max_score),
            ),
        )

    result = AIMarkingResult(
        university_id=university_id,
        job_id=job_id,
        submission_id=submission_id,
        question_id=question_id,
        student_id=student_id,
        extracted_answer=extracted_answer,
        suggested_score=suggested_score,
        max_score=max_score,
        confidence=confidence,
        grading_evidence=grading_evidence,
        feedback=feedback,
        status="pending_review",
        ai_provider=ai_provider,
        ai_model=ai_model,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result


# ============================================================
# AI MARKING
# ============================================================

def mark_answer_with_ai(
    question: AssessmentQuestion,
    answer: str,
) -> dict:
    """
    Mark ONE student's answer against ONE question.

    The caller must provide ONLY the answer belonging
    to this question.
    """

    answer = (
        answer or ""
    ).strip()

    # Missing answer must never be sent as useful content.
    if not answer:
        return {
            "score": 0.0,
            "confidence": 1.0,
            "grading_evidence": (
                "No answer was detected for this question."
            ),
            "feedback": (
                "No answer was detected for this question."
            ),
        }

    prompt = f"""
You are an academic marking assistant.

You are marking ONE student's answer to ONE question.

QUESTION:

{question.question_text}

MAXIMUM MARK:

{question.max_score}

MODEL ANSWER:

{question.model_answer or "No model answer provided."}

MARKING SCHEME:

{question.marking_scheme or "No marking scheme provided."}

STUDENT ANSWER:

{answer}

Rules:

1. Mark ONLY the student's answer provided above.
2. Do not use information from other questions.
3. Do not assume the student wrote information that is not present.
4. Award a score from 0 to the maximum mark.
5. Give partial marks where justified.
6. Compare the answer directly against the question.
7. Use the model answer and marking scheme when available.
8. Do not invent facts.
9. Be academically fair and conservative.
10. Grading evidence must refer only to observable content in the student's answer.
11. Feedback should be brief and constructive.
12. Return JSON only.

Required JSON:

{{
    "score": 0,
    "confidence": 0.0,
    "grading_evidence": "Brief evidence supporting the score.",
    "feedback": "Brief constructive feedback to the student."
}}
"""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    raw = data.get(
        "response",
        "{}",
    )

    try:
        result = json.loads(raw)

    except json.JSONDecodeError:
        raise ValueError(
            "Ollama returned invalid JSON while marking the answer."
        )

    try:
        score = float(
            result.get(
                "score",
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        score = 0.0

    try:
        confidence = float(
            result.get(
                "confidence",
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        confidence = 0.0

    score = max(
        0.0,
        min(
            score,
            float(question.max_score),
        ),
    )

    confidence = max(
        0.0,
        min(
            confidence,
            1.0,
        ),
    )

    return {
        "score": score,
        "confidence": confidence,
        "grading_evidence": str(
            result.get(
                "grading_evidence",
                "",
            )
        ),
        "feedback": str(
            result.get(
                "feedback",
                "",
            )
        ),
    }
