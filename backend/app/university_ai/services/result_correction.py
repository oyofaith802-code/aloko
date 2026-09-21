from datetime import datetime

from sqlalchemy.orm import Session

from app.university_ai.models.assessment import (
    StudentScore,
    ResultSheet,
)

from app.university_ai.services.result_audit import (
    ResultCorrectionAudit,
)


def request_score_correction(
    db: Session,
    university_id: int,
    student_score_id: int,
    new_score: float,
    reason: str,
    requested_by: int,
):
    if not reason or not reason.strip():
        raise ValueError("Correction reason is required.")

    score_record = (
        db.query(StudentScore)
        .filter(
            StudentScore.id == student_score_id,
            StudentScore.university_id == university_id,
        )
        .first()
    )

    if not score_record:
        raise ValueError("Student score not found.")

    if new_score < 0:
        raise ValueError("Score cannot be negative.")

    assessment_max = None

    from app.university_ai.models.assessment import Assessment

    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == score_record.assessment_id)
        .first()
    )

    if assessment:
        assessment_max = assessment.max_score

    if assessment_max is not None and new_score > assessment_max:
        raise ValueError(
            f"Score cannot exceed maximum score of {assessment_max}."
        )

    old_score = score_record.score
    old_percentage = score_record.percentage

    if assessment_max:
        new_percentage = (
            new_score / assessment_max
        ) * 100
    else:
        new_percentage = None

    audit = ResultCorrectionAudit(
        university_id=university_id,
        student_id=score_record.student_id,
        course_offering_id=score_record.course_offering_id,
        student_score_id=score_record.id,
        old_score=old_score,
        new_score=new_score,
        old_percentage=old_percentage,
        new_percentage=new_percentage,
        reason=reason.strip(),
        status="pending",
        requested_by=requested_by,
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit


def approve_score_correction(
    db: Session,
    audit_id: int,
    approved_by: int,
):
    audit = (
        db.query(ResultCorrectionAudit)
        .filter(ResultCorrectionAudit.id == audit_id)
        .first()
    )

    if not audit:
        raise ValueError("Correction request not found.")

    if audit.status != "pending":
        raise ValueError(
            f"Correction is already {audit.status}."
        )

    score_record = None

    if audit.student_score_id:
        score_record = (
            db.query(StudentScore)
            .filter(
                StudentScore.id == audit.student_score_id
            )
            .first()
        )

    if not score_record:
        raise ValueError(
            "Original student score no longer exists."
        )

    score_record.score = audit.new_score
    score_record.percentage = audit.new_percentage
    score_record.marked_by = approved_by
    score_record.marked_at = datetime.utcnow()
    score_record.status = "marked"

    audit.status = "approved"
    audit.approved_by = approved_by
    audit.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(audit)

    return audit


def reject_score_correction(
    db: Session,
    audit_id: int,
    rejected_by: int,
    reason: str = None,
):
    audit = (
        db.query(ResultCorrectionAudit)
        .filter(ResultCorrectionAudit.id == audit_id)
        .first()
    )

    if not audit:
        raise ValueError("Correction request not found.")

    if audit.status != "pending":
        raise ValueError(
            f"Correction is already {audit.status}."
        )

    audit.status = "rejected"
    audit.approved_by = rejected_by
    audit.approved_at = datetime.utcnow()

    if reason:
        audit.reason = (
            f"{audit.reason}\n"
            f"Rejection: {reason.strip()}"
        )

    db.commit()
    db.refresh(audit)

    return audit


def get_result_correction_history(
    db: Session,
    university_id: int,
    student_id: int = None,
    course_offering_id: int = None,
):
    query = (
        db.query(ResultCorrectionAudit)
        .filter(
            ResultCorrectionAudit.university_id
            == university_id
        )
    )

    if student_id is not None:
        query = query.filter(
            ResultCorrectionAudit.student_id == student_id
        )

    if course_offering_id is not None:
        query = query.filter(
            ResultCorrectionAudit.course_offering_id
            == course_offering_id
        )

    return (
        query
        .order_by(
            ResultCorrectionAudit.created_at.desc()
        )
        .all()
    )


def get_pending_corrections(
    db: Session,
    university_id: int,
):
    return (
        db.query(ResultCorrectionAudit)
        .filter(
            ResultCorrectionAudit.university_id
            == university_id,
            ResultCorrectionAudit.status == "pending",
        )
        .order_by(
            ResultCorrectionAudit.created_at.desc()
        )
        .all()
    )