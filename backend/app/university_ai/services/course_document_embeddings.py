import json
import re
from typing import List

from sqlalchemy.orm import Session
from app.university_ai.models.course_document import CourseDocument
from app.university_ai.models.course_document_chunk import CourseDocumentChunk


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

_embedding_model = None


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return _embedding_model


def clean_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    text = clean_text(text)

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def build_course_document_chunks(
    db: Session,
    document: CourseDocument,
) -> int:
    text = clean_text(document.extracted_text)

    if not text:
        raise ValueError(
            "This course document has no extracted text to index."
        )

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError(
            "No usable text chunks were created from this document."
        )

    model = get_embedding_model()

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    db.query(CourseDocumentChunk).filter(
        CourseDocumentChunk.document_id == document.id
    ).delete(
        synchronize_session=False
    )

    for index, (content, embedding) in enumerate(
        zip(chunks, embeddings)
    ):
        db.add(
            CourseDocumentChunk(
                university_id=document.university_id,
                course_offering_id=document.course_offering_id,
                document_id=document.id,
                chunk_index=index,
                content=content,
                embedding=json.dumps(
                    embedding.tolist()
                ),
            )
        )

    db.commit()

    return len(chunks)


