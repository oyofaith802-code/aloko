from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class AssessmentQuestion(Base):
    __tablename__ = "university_assessment_questions"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    assessment_id = Column(Integer, nullable=False, index=True)

    question_number = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)

    max_score = Column(Float, nullable=False)

    model_answer = Column(Text, nullable=True)
    marking_scheme = Column(Text, nullable=True)

    created_by = Column(Integer, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AssessmentSubmission(Base):
    __tablename__ = "university_assessment_submissions"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    assessment_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=True, index=True)

    file_name = Column(String(255), nullable=True)
    file_path = Column(Text, nullable=True)

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


class AIMarkingJob(Base):
    __tablename__ = "university_ai_marking_jobs"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    assessment_id = Column(Integer, nullable=False, index=True)

    submission_ids = Column(Text, nullable=True)

    created_by = Column(Integer, nullable=False, index=True)

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    total_submissions = Column(Integer, nullable=False, default=0)
    processed_submissions = Column(Integer, nullable=False, default=0)

    ai_provider = Column(String(100), nullable=True)
    ai_model = Column(String(150), nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AIMarkingResult(Base):
    __tablename__ = "university_ai_marking_results"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    job_id = Column(Integer, nullable=False, index=True)
    submission_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False, index=True)

    student_id = Column(Integer, nullable=True, index=True)

    extracted_answer = Column(Text, nullable=True)

    suggested_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=False)

    confidence = Column(Float, nullable=True)

    grading_evidence = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="pending_review",
        server_default="pending_review",
        index=True,
    )

    lecturer_score = Column(Float, nullable=True)
    lecturer_comment = Column(Text, nullable=True)

    reviewed_by = Column(Integer, nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    ai_provider = Column(String(100), nullable=True)
    ai_model = Column(String(150), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )



