from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database.connection import Base

from app.university_ai.models.assessment import (
    StudentScore,
    ResultSheet,
)


class ResultCorrectionAudit(Base):
    __tablename__ = "university_result_correction_audits"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    result_sheet_id = Column(Integer, nullable=True, index=True)
    student_score_id = Column(Integer, nullable=True, index=True)

    old_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)

    old_percentage = Column(Float, nullable=True)
    new_percentage = Column(Float, nullable=True)

    reason = Column(Text, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    requested_by = Column(Integer, nullable=False, index=True)
    approved_by = Column(Integer, nullable=True, index=True)

    requested_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )