import json
import requests
from typing import List

from sqlalchemy.orm import Session

from app.university_ai.models import StudentCourse
from app.university_ai.services.course_document_search import search_course_documents


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def verify_course_enrollment(
    db: Session,
    student_id: int,
    university_id: int,
    course_offering_id: int,
) -> bool:
    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.university_id == university_id,
            StudentCourse.student_id == student_id,
            StudentCourse.course_offering_id == course_offering_id,
            StudentCourse.enrollment_status == "enrolled",
        )
        .first()
    )

    return enrollment is not None


def ask_course_ai(
    db: Session,
    student_id: int,
    university_id: int,
    course_offering_id: int,
    question: str,
    top_k: int = 5,
) -> dict:
    question = str(question or "").strip()

    if not question:
        raise ValueError("Question is required.")

    if not verify_course_enrollment(
        db=db,
        student_id=student_id,
        university_id=university_id,
        course_offering_id=course_offering_id,
    ):
        raise PermissionError(
            "You are not enrolled in this course."
        )

    sources = search_course_documents(
        db=db,
        university_id=university_id,
        course_offering_id=course_offering_id,
        query=question,
        top_k=top_k,
    )

    if not sources:
        return {
            "answer": (
                "I could not find any course materials for this course. "
                "Please ask your lecturer to upload the relevant textbook "
                "or course documents."
            ),
            "sources": [],
            "model": OLLAMA_MODEL,
        }

    context_parts: List[str] = []

    for index, source in enumerate(sources, start=1):
        context_parts.append(
            f"""
SOURCE {index}
DOCUMENT: {source["document_title"]}
CONTENT:
{source["content"]}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are Aloko University AI, an academic course assistant.

Answer the student's question using ONLY the course material supplied
below.

If the answer cannot be supported by the supplied course material,
say clearly that the available course materials do not contain enough
information to answer confidently.

Do not invent textbook content.
Do not claim information came from a source when it did not.
Explain concepts clearly and simply while preserving academic accuracy.

STUDENT QUESTION:
{question}

COURSE MATERIAL:
{context}

Return JSON only:

{{
    "answer": "Write the actual answer to the student question using the supplied course material. Do not copy this instruction.",
    "source_numbers": [1]
}}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    raw = data.get("response", "{}")

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(
            "Ollama returned invalid JSON while answering the course question."
        )

    answer = str(
        result.get("answer") or ""
    ).strip()

    if not answer:
        answer = (
            "I could not generate a reliable answer from the available "
            "course materials."
        )

    source_numbers = result.get("source_numbers", [])

    if not isinstance(source_numbers, list):
        source_numbers = []

    selected_sources = []

    for number in source_numbers:
        try:
            index = int(number) - 1
        except (TypeError, ValueError):
            continue

        if 0 <= index < len(sources):
            selected_sources.append(
                {
                    "document_id": sources[index]["document_id"],
                    "document_title": sources[index]["document_title"],
                    "chunk_id": sources[index]["chunk_id"],
                    "score": sources[index]["score"],
                }
            )

    if not selected_sources:
        selected_sources = [
            {
                "document_id": source["document_id"],
                "document_title": source["document_title"],
                "chunk_id": source["chunk_id"],
                "score": source["score"],
            }
            for source in sources
        ]

    return {
        "answer": answer,
        "sources": selected_sources,
        "model": OLLAMA_MODEL,
    }

