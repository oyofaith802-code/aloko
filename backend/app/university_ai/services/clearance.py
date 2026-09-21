from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.university_ai.models.clearance import (
    ClearanceConfiguration,
    ClearanceStage,
    ClearanceRequirement,
    StudentClearance,
    StudentClearanceStage,
    ClearanceAudit,
)


# ============================================================
# VALIDATION
# ============================================================

VALID_CLEARANCE_STATUSES = {
    "pending",
    "in_progress",
    "approved",
    "rejected",
    "completed",
}

VALID_STAGE_STATUSES = {
    "pending",
    "in_progress",
    "approved",
    "rejected",
    "completed",
}


def _now():
    return datetime.now(timezone.utc)


def validate_status(status: str):
    if status not in VALID_CLEARANCE_STATUSES:
        raise ValueError(f"Invalid clearance status: {status}")
    return status


# ============================================================
# CONFIGURATION
# ============================================================

def create_clearance_configuration(
    db: Session,
    university_id: int,
    name: str = "Student Clearance",
    description: str | None = None,
    requires_payment: bool = False,
):
    existing = (
        db.query(ClearanceConfiguration)
        .filter(
            ClearanceConfiguration.university_id == university_id
        )
        .first()
    )

    if existing:
        raise ValueError(
            "Clearance configuration already exists for this university"
        )

    config = ClearanceConfiguration(
        university_id=university_id,
        name=name,
        description=description,
        requires_payment=requires_payment,
        is_enabled=True,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def get_clearance_configuration(
    db: Session,
    university_id: int,
):
    return (
        db.query(ClearanceConfiguration)
        .filter(
            ClearanceConfiguration.university_id == university_id
        )
        .first()
    )


def update_clearance_configuration(
    db: Session,
    university_id: int,
    name: str | None = None,
    description: str | None = None,
    is_enabled: bool | None = None,
    requires_payment: bool | None = None,
):
    config = get_clearance_configuration(db, university_id)

    if not config:
        raise ValueError("Clearance configuration not found")

    if name is not None:
        config.name = name

    if description is not None:
        config.description = description

    if is_enabled is not None:
        config.is_enabled = is_enabled

    if requires_payment is not None:
        config.requires_payment = requires_payment

    db.commit()
    db.refresh(config)

    return config


# ============================================================
# CLEARANCE STAGES
# ============================================================

def add_clearance_stage(
    db: Session,
    university_id: int,
    name: str,
    code: str,
    stage_order: int,
    officer_role: str | None = None,
    is_required: bool = True,
    requires_payment: bool = False,
    description: str | None = None,
):
    config = get_clearance_configuration(db, university_id)

    if not config:
        raise ValueError("Clearance configuration not found")

    existing = (
        db.query(ClearanceStage)
        .filter(
            ClearanceStage.university_id == university_id,
            ClearanceStage.code == code,
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Clearance stage '{code}' already exists"
        )

    stage = ClearanceStage(
        university_id=university_id,
        configuration_id=config.id,
        name=name,
        code=code,
        description=description,
        stage_order=stage_order,
        officer_role=officer_role,
        is_required=is_required,
        requires_payment=requires_payment,
        status="active",
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage


def list_clearance_stages(
    db: Session,
    university_id: int,
    active_only: bool = True,
):
    query = (
        db.query(ClearanceStage)
        .filter(
            ClearanceStage.university_id == university_id
        )
    )

    if active_only:
        query = query.filter(
            ClearanceStage.status == "active"
        )

    return query.order_by(
        ClearanceStage.stage_order.asc()
    ).all()


def update_clearance_stage(
    db: Session,
    university_id: int,
    stage_id: int,
    name: str | None = None,
    stage_order: int | None = None,
    officer_role: str | None = None,
    is_required: bool | None = None,
    requires_payment: bool | None = None,
    description: str | None = None,
):
    stage = (
        db.query(ClearanceStage)
        .filter(
            ClearanceStage.id == stage_id,
            ClearanceStage.university_id == university_id,
        )
        .first()
    )

    if not stage:
        raise ValueError("Clearance stage not found")

    if name is not None:
        stage.name = name

    if stage_order is not None:
        stage.stage_order = stage_order

    if officer_role is not None:
        stage.officer_role = officer_role

    if is_required is not None:
        stage.is_required = is_required

    if requires_payment is not None:
        stage.requires_payment = requires_payment

    if description is not None:
        stage.description = description

    db.commit()
    db.refresh(stage)

    return stage


def deactivate_clearance_stage(
    db: Session,
    university_id: int,
    stage_id: int,
):
    stage = (
        db.query(ClearanceStage)
        .filter(
            ClearanceStage.id == stage_id,
            ClearanceStage.university_id == university_id,
        )
        .first()
    )

    if not stage:
        raise ValueError("Clearance stage not found")

    stage.status = "inactive"

    db.commit()
    db.refresh(stage)

    return stage


# ============================================================
# REQUIREMENTS
# ============================================================

def add_clearance_requirement(
    db: Session,
    university_id: int,
    stage_id: int,
    name: str,
    requirement_type: str = "verification",
    description: str | None = None,
    is_required: bool = True,
):
    stage = (
        db.query(ClearanceStage)
        .filter(
            ClearanceStage.id == stage_id,
            ClearanceStage.university_id == university_id,
        )
        .first()
    )

    if not stage:
        raise ValueError("Clearance stage not found")

    requirement = ClearanceRequirement(
        university_id=university_id,
        stage_id=stage_id,
        name=name,
        requirement_type=requirement_type,
        description=description,
        is_required=is_required,
        status="active",
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


def list_clearance_requirements(
    db: Session,
    university_id: int,
    stage_id: int | None = None,
):
    query = (
        db.query(ClearanceRequirement)
        .filter(
            ClearanceRequirement.university_id == university_id,
            ClearanceRequirement.status == "active",
        )
    )

    if stage_id is not None:
        query = query.filter(
            ClearanceRequirement.stage_id == stage_id
        )

    return query.order_by(
        ClearanceRequirement.id.asc()
    ).all()


# ============================================================
# AUDIT
# ============================================================

def _create_audit(
    db: Session,
    university_id: int,
    clearance_id: int,
    action: str,
    performed_by: int,
    old_status: str | None = None,
    new_status: str | None = None,
    clearance_stage_id: int | None = None,
    reason: str | None = None,
):
    audit = ClearanceAudit(
        university_id=university_id,
        clearance_id=clearance_id,
        clearance_stage_id=clearance_stage_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        performed_by=performed_by,
        reason=reason,
    )

    db.add(audit)

    return audit


def get_clearance_history(
    db: Session,
    university_id: int,
    clearance_id: int,
):
    return (
        db.query(ClearanceAudit)
        .filter(
            ClearanceAudit.university_id == university_id,
            ClearanceAudit.clearance_id == clearance_id,
        )
        .order_by(ClearanceAudit.created_at.asc())
        .all()
    )


# ============================================================
# STUDENT CLEARANCE
# ============================================================

def create_student_clearance(
    db: Session,
    university_id: int,
    student_id: int,
    academic_session_id: int | None = None,
    clearance_type: str = "general",
    created_by: int | None = None,
):
    existing = (
        db.query(StudentClearance)
        .filter(
            StudentClearance.university_id == university_id,
            StudentClearance.student_id == student_id,
            StudentClearance.clearance_type == clearance_type,
            StudentClearance.status.in_(
                ["pending", "in_progress"]
            ),
        )
        .first()
    )

    if existing:
        raise ValueError(
            "Student already has an active clearance"
        )

    config = get_clearance_configuration(db, university_id)

    if not config:
        raise ValueError("Clearance configuration not found")

    if not config.is_enabled:
        raise ValueError("Clearance is currently disabled")

    stages = list_clearance_stages(
        db,
        university_id,
        active_only=True,
    )

    required_stages = [
        stage for stage in stages
        if stage.is_required
    ]

    if not required_stages:
        raise ValueError(
            "No required clearance stages configured"
        )

    payment_status = (
        "pending"
        if config.requires_payment
        else "not_required"
    )

    clearance = StudentClearance(
        university_id=university_id,
        student_id=student_id,
        academic_session_id=academic_session_id,
        clearance_type=clearance_type,
        status="pending",
        payment_status=payment_status,
    )

    db.add(clearance)
    db.flush()

    for stage in required_stages:
        student_stage = StudentClearanceStage(
            university_id=university_id,
            clearance_id=clearance.id,
            stage_id=stage.id,
            status="pending",
        )

        db.add(student_stage)

    if created_by is not None:
        _create_audit(
            db=db,
            university_id=university_id,
            clearance_id=clearance.id,
            action="created",
            performed_by=created_by,
            new_status="pending",
        )

    db.commit()
    db.refresh(clearance)

    return clearance


def get_student_clearance(
    db: Session,
    university_id: int,
    clearance_id: int,
):
    return (
        db.query(StudentClearance)
        .filter(
            StudentClearance.id == clearance_id,
            StudentClearance.university_id == university_id,
        )
        .first()
    )


def get_student_clearances(
    db: Session,
    university_id: int,
    student_id: int,
):
    return (
        db.query(StudentClearance)
        .filter(
            StudentClearance.university_id == university_id,
            StudentClearance.student_id == student_id,
        )
        .order_by(
            StudentClearance.created_at.desc()
        )
        .all()
    )


def get_clearance_stages_for_student(
    db: Session,
    university_id: int,
    clearance_id: int,
):
    return (
        db.query(StudentClearanceStage)
        .filter(
            StudentClearanceStage.university_id == university_id,
            StudentClearanceStage.clearance_id == clearance_id,
        )
        .join(
            ClearanceStage,
            StudentClearanceStage.stage_id == ClearanceStage.id,
        )
        .order_by(
            ClearanceStage.stage_order.asc()
        )
        .all()
    )


# ============================================================
# SUBMIT / RESUBMIT
# ============================================================

def submit_clearance(
    db: Session,
    university_id: int,
    clearance_id: int,
    student_id: int,
):
    clearance = get_student_clearance(
        db,
        university_id,
        clearance_id,
    )

    if not clearance:
        raise ValueError("Clearance not found")

    if clearance.student_id != student_id:
        raise ValueError("Clearance does not belong to student")

    if clearance.status not in {
        "pending",
        "rejected",
    }:
        raise ValueError(
            f"Clearance cannot be submitted from status "
            f"'{clearance.status}'"
        )

    stages = get_clearance_stages_for_student(
        db,
        university_id,
        clearance_id,
    )

    for student_stage in stages:
        if student_stage.status == "rejected":
            student_stage.status = "pending"
            student_stage.rejection_reason = None
            student_stage.officer_comment = None
            student_stage.rejected_at = None

    old_status = clearance.status

    clearance.status = "in_progress"
    clearance.submitted_at = _now()
    clearance.rejection_reason = None

    _create_audit(
        db=db,
        university_id=university_id,
        clearance_id=clearance.id,
        action="submitted",
        performed_by=student_id,
        old_status=old_status,
        new_status="in_progress",
    )

    db.commit()
    db.refresh(clearance)

    return clearance


# ============================================================
# STAGE APPROVAL / REJECTION
# ============================================================

def approve_clearance_stage(
    db: Session,
    university_id: int,
    clearance_id: int,
    student_stage_id: int,
    officer_id: int,
    comment: str | None = None,
):
    clearance = get_student_clearance(
        db,
        university_id,
        clearance_id,
    )

    if not clearance:
        raise ValueError("Clearance not found")

    stage = (
        db.query(StudentClearanceStage)
        .filter(
            StudentClearanceStage.id == student_stage_id,
            StudentClearanceStage.university_id == university_id,
            StudentClearanceStage.clearance_id == clearance_id,
        )
        .first()
    )

    if not stage:
        raise ValueError("Student clearance stage not found")

    if stage.status == "approved":
        raise ValueError("Stage is already approved")

    old_status = stage.status

    stage.status = "approved"
    stage.officer_id = officer_id
    stage.officer_comment = comment
    stage.approved_at = _now()
    stage.rejected_at = None
    stage.rejection_reason = None

    _create_audit(
        db=db,
        university_id=university_id,
        clearance_id=clearance_id,
        clearance_stage_id=stage.id,
        action="stage_approved",
        performed_by=officer_id,
        old_status=old_status,
        new_status="approved",
        reason=comment,
    )

    _update_clearance_progress(
        db,
        clearance,
        officer_id,
    )

    db.commit()
    db.refresh(clearance)

    return clearance


def reject_clearance_stage(
    db: Session,
    university_id: int,
    clearance_id: int,
    student_stage_id: int,
    officer_id: int,
    reason: str,
):
    if not reason or not reason.strip():
        raise ValueError(
            "Rejection reason is required"
        )

    clearance = get_student_clearance(
        db,
        university_id,
        clearance_id,
    )

    if not clearance:
        raise ValueError("Clearance not found")

    stage = (
        db.query(StudentClearanceStage)
        .filter(
            StudentClearanceStage.id == student_stage_id,
            StudentClearanceStage.university_id == university_id,
            StudentClearanceStage.clearance_id == clearance_id,
        )
        .first()
    )

    if not stage:
        raise ValueError("Student clearance stage not found")

    old_status = stage.status

    stage.status = "rejected"
    stage.officer_id = officer_id
    stage.rejection_reason = reason.strip()
    stage.rejected_at = _now()

    clearance.status = "rejected"
    clearance.rejection_reason = reason.strip()

    _create_audit(
        db=db,
        university_id=university_id,
        clearance_id=clearance_id,
        clearance_stage_id=stage.id,
        action="stage_rejected",
        performed_by=officer_id,
        old_status=old_status,
        new_status="rejected",
        reason=reason.strip(),
    )

    db.commit()
    db.refresh(clearance)

    return clearance


# ============================================================
# PROGRESS ENGINE
# ============================================================

def _update_clearance_progress(
    db: Session,
    clearance: StudentClearance,
    performed_by: int,
):
    stages = get_clearance_stages_for_student(
        db,
        clearance.university_id,
        clearance.id,
    )

    if not stages:
        return

    rejected = any(
        stage.status == "rejected"
        for stage in stages
    )

    if rejected:
        clearance.status = "rejected"
        return

    all_approved = all(
        stage.status == "approved"
        for stage in stages
    )

    if all_approved:
        old_status = clearance.status

        clearance.status = "completed"
        clearance.completed_at = _now()
        clearance.final_approved_by = performed_by
        clearance.final_approved_at = _now()

        _create_audit(
            db=db,
            university_id=clearance.university_id,
            clearance_id=clearance.id,
            action="clearance_completed",
            performed_by=performed_by,
            old_status=old_status,
            new_status="completed",
        )

        return

    clearance.status = "in_progress"


def get_clearance_progress(
    db: Session,
    university_id: int,
    clearance_id: int,
):
    clearance = get_student_clearance(
        db,
        university_id,
        clearance_id,
    )

    if not clearance:
        raise ValueError("Clearance not found")

    stages = get_clearance_stages_for_student(
        db,
        university_id,
        clearance_id,
    )

    total = len(stages)
    approved = sum(
        1 for stage in stages
        if stage.status == "approved"
    )
    rejected = sum(
        1 for stage in stages
        if stage.status == "rejected"
    )

    percentage = (
        (approved / total) * 100
        if total
        else 0
    )

    return {
        "clearance_id": clearance.id,
        "student_id": clearance.student_id,
        "status": clearance.status,
        "payment_status": clearance.payment_status,
        "total_stages": total,
        "approved_stages": approved,
        "rejected_stages": rejected,
        "pending_stages": total - approved - rejected,
        "progress_percentage": round(percentage, 2),
        "completed": clearance.status == "completed",
    }


# ============================================================
# FINAL APPROVAL
# ============================================================

def finalize_clearance(
    db: Session,
    university_id: int,
    clearance_id: int,
    officer_id: int,
):
    clearance = get_student_clearance(
        db,
        university_id,
        clearance_id,
    )

    if not clearance:
        raise ValueError("Clearance not found")

    stages = get_clearance_stages_for_student(
        db,
        university_id,
        clearance_id,
    )

    if not stages:
        raise ValueError(
            "No clearance stages found"
        )

    if any(
        stage.status != "approved"
        for stage in stages
    ):
        raise ValueError(
            "All required clearance stages must be approved"
        )

    if clearance.payment_status not in {
        "not_required",
        "paid",
        "verified",
    }:
        raise ValueError(
            "Required clearance payment has not been verified"
        )

    old_status = clearance.status

    clearance.status = "completed"
    clearance.completed_at = _now()
    clearance.final_approved_by = officer_id
    clearance.final_approved_at = _now()

    _create_audit(
        db=db,
        university_id=university_id,
        clearance_id=clearance.id,
        action="final_approval",
        performed_by=officer_id,
        old_status=old_status,
        new_status="completed",
    )

    db.commit()
    db.refresh(clearance)

    return clearance