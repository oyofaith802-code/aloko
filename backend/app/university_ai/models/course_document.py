from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class CourseDocument(Base):
    __tablename__ = "university_course_documents"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)
    lecturer_id = Column(Integer, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)

    file_path = Column(Text, nullable=True)
    file_type = Column(String(50), nullable=False)

    extracted_text = Column(Text, nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
