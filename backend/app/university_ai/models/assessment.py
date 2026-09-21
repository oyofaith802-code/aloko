from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class Assessment(Base):
    __tablename__ = "university_assessments"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    assessment_type = Column(String(50), nullable=False, index=True)

    description = Column(Text, nullable=True)

    max_score = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)

    assessment_date = Column(DateTime(timezone=True), nullable=True)

    is_published = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    created_by = Column(Integer, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class StudentScore(Base):
    __tablename__ = "university_student_scores"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    student_id = Column(Integer, nullable=False, index=True)
    assessment_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    score = Column(Float, nullable=True)

    percentage = Column(Float, nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    is_absent = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    lecturer_comment = Column(Text, nullable=True)

    marked_by = Column(Integer, nullable=True, index=True)

    marked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ResultSheet(Base):
    __tablename__ = "university_result_sheets"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    student_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    total_score = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)

    grade = Column(String(10), nullable=True)
    grade_point = Column(Float, nullable=True)

    credit_units = Column(Integer, nullable=True)

    remarks = Column(String(255), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    generated_by = Column(Integer, nullable=True, index=True)

    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )