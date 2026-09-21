import json
from typing import List

from sqlalchemy.orm import Session

from app.university_ai.models.course_document_chunk import CourseDocumentChunk
from app.university_ai.models.course_document import CourseDocument
from app.university_ai.services.course_document_embeddings import get_embedding_model


def search_course_documents(
    db: Session,
    university_id: int,
    course_offering_id: int,
    query: str,
    top_k: int = 5,
) -> List[dict]:
    query = str(query or "").strip()

    if not query:
        return []

    model = get_embedding_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    chunks = (
        db.query(
            CourseDocumentChunk,
            CourseDocument.title,
        )
        .join(
            CourseDocument,
            CourseDocument.id == CourseDocumentChunk.document_id,
        )
        .filter(
            CourseDocumentChunk.university_id == university_id,
            CourseDocumentChunk.course_offering_id == course_offering_id,
        )
        .all()
    )

    scored = []

    for chunk, document_title in chunks:
        try:
            stored_embedding = json.loads(chunk.embedding)
        except Exception:
            continue

        if not stored_embedding:
            continue

        score = sum(
            float(a) * float(b)
            for a, b in zip(query_embedding, stored_embedding)
        )

        scored.append(
            {
                "document_id": chunk.document_id,
                "document_title": document_title,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "score": float(score),
            }
        )

    scored.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored[: max(1, int(top_k))]
