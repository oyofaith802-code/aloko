from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.connection import Base


class CourseDocumentChunk(Base):
    __tablename__ = "university_course_document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)
    document_id = Column(
        Integer,
        ForeignKey("university_course_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
