from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func

from app.database.connection import Base


class ClearanceConfiguration(Base):
    __tablename__ = "university_clearance_configurations"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, nullable=False, unique=True, index=True)

    name = Column(String(255), nullable=False, default="Student Clearance")
    description = Column(Text, nullable=True)

    is_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    requires_payment = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClearanceStage(Base):
    __tablename__ = "university_clearance_stages"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    configuration_id = Column(Integer, nullable=False, index=True)

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False, index=True)

    description = Column(Text, nullable=True)

    stage_order = Column(Integer, nullable=False, default=1)

    officer_role = Column(String(100), nullable=True)

    is_required = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    requires_payment = Column(
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClearanceRequirement(Base):
    __tablename__ = "university_clearance_requirements"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    stage_id = Column(Integer, nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    requirement_type = Column(
        String(50),
        nullable=False,
        default="verification",
    )

    is_required = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class StudentClearance(Base):
    __tablename__ = "university_student_clearances"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)

    academic_session_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    clearance_type = Column(
        String(100),
        nullable=False,
        default="general",
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    payment_status = Column(
        String(50),
        nullable=False,
        default="not_required",
        index=True,
    )

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    final_approved_by = Column(
        Integer,
        nullable=True,
        index=True,
    )

    final_approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class StudentClearanceStage(Base):
    __tablename__ = "university_student_clearance_stages"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    clearance_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    stage_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    officer_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    officer_comment = Column(Text, nullable=True)

    rejection_reason = Column(Text, nullable=True)

    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClearanceAudit(Base):
    __tablename__ = "university_clearance_audits"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    clearance_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    clearance_stage_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    action = Column(String(100), nullable=False)

    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)

    performed_by = Column(
        Integer,
        nullable=False,
        index=True,
    )

    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())