from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User

from app.university_ai.services.university_admin_auth import (
    require_university_admin,
    require_university_access,
)
from app.university_ai.services.student_auth import require_student

from app.university_ai.services.clearance import (
    create_clearance_configuration,
    get_clearance_configuration,
    update_clearance_configuration,
    add_clearance_stage,
    list_clearance_stages,
    update_clearance_stage,
    deactivate_clearance_stage,
    add_clearance_requirement,
    list_clearance_requirements,
    create_student_clearance,
    get_student_clearance,
    get_student_clearances,
    get_clearance_stages_for_student,
    submit_clearance,
    approve_clearance_stage,
    reject_clearance_stage,
    get_clearance_progress,
    finalize_clearance,
)


router = APIRouter(
    prefix="/university/clearance",
    tags=["University Clearance"],
)


class ClearanceConfigCreate(BaseModel):
    university_id: int
    name: str = "Student Clearance"
    description: str | None = None
    payment_required: bool = False
    status: str = "active"


class ClearanceConfigUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    payment_required: bool | None = None
    status: str | None = None


class ClearanceStageCreate(BaseModel):
    university_id: int
    name: str
    code: str
    description: str | None = None
    stage_order: int = 1
    requires_payment: bool = False
    status: str = "active"


class ClearanceStageUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    stage_order: int | None = None
    requires_payment: bool | None = None
    status: str | None = None


class ClearanceRequirementCreate(BaseModel):
    university_id: int
    clearance_stage_id: int
    name: str
    code: str
    description: str | None = None
    is_required: bool = True
    status: str = "active"


class StudentClearanceCreate(BaseModel):
    university_id: int
    student_id: int
    clearance_configuration_id: int | None = None


class ClearanceSubmit(BaseModel):
    clearance_id: int


class ClearanceStageDecision(BaseModel):
    university_id: int
    student_clearance_id: int
    student_clearance_stage_id: int
    notes: str | None = None


class ClearanceStageReject(BaseModel):
    university_id: int
    student_clearance_id: int
    student_clearance_stage_id: int
    reason: str


class ClearanceFinalize(BaseModel):
    university_id: int
    student_clearance_id: int


# ============================================================
# CONFIGURATION
# ============================================================

@router.post("/config")
def create_config(
    payload: ClearanceConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return create_clearance_configuration(
            db=db,
            university_id=payload.university_id,
            name=payload.name,
            description=payload.description,
            requires_payment=payload.payment_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/{university_id}")
def get_config(
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    try:
        result = get_clearance_configuration(
            db,
            university_id,
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Clearance configuration not found",
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/config/{university_id}")
def update_config(
    university_id: int,
    payload: ClearanceConfigUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    try:
        return update_clearance_configuration(
            db=db,
            university_id=university_id,
            name=payload.name,
            description=payload.description,
            is_enabled=(
                payload.status == "active"
                if payload.status is not None
                else None
            ),
            requires_payment=payload.payment_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# STAGES
# ============================================================

@router.post("/stages")
def create_stage(
    payload: ClearanceStageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return add_clearance_stage(
            db=db,
            university_id=payload.university_id,
            name=payload.name,
            code=payload.code,
            stage_order=payload.stage_order,
            description=payload.description,
            requires_payment=payload.requires_payment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stages/{university_id}")
def get_stages(
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return list_clearance_stages(
        db,
        university_id,
    )


@router.put("/stages/{stage_id}")
def edit_stage(
    stage_id: int,
    university_id: int,
    payload: ClearanceStageUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    try:
        return update_clearance_stage(
            db=db,
            university_id=university_id,
            stage_id=stage_id,
            name=payload.name,
            stage_order=payload.stage_order,
            description=payload.description,
            requires_payment=payload.requires_payment,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/stages/{stage_id}")
def disable_stage(
    stage_id: int,
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    try:
        return deactivate_clearance_stage(
            db=db,
            university_id=university_id,
            stage_id=stage_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# REQUIREMENTS
# ============================================================

@router.post("/requirements")
def create_requirement(
    payload: ClearanceRequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return add_clearance_requirement(
            db=db,
            university_id=payload.university_id,
            stage_id=payload.clearance_stage_id,
            name=payload.name,
            requirement_type=payload.code,
            description=payload.description,
            is_required=payload.is_required,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requirements/{stage_id}")
def get_requirements(
    stage_id: int,
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return list_clearance_requirements(
        db=db,
        university_id=university_id,
        stage_id=stage_id,
    )


# ============================================================
# STUDENT CLEARANCE
# ============================================================

@router.post("/students")
def create_student_clearance_route(
    payload: StudentClearanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return create_student_clearance(
            db=db,
            university_id=payload.university_id,
            student_id=payload.student_id,
            created_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/students/{university_id}/{student_id}")
def get_student_clearance_route(
    university_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    if (
        student.university_id != university_id
        or student.id != student_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only access your own clearance.",
        )

    return get_student_clearances(
        db=db,
        university_id=university_id,
        student_id=student_id,
    )


@router.get("/students/{university_id}")
def get_student_clearances_route(
    university_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return get_student_clearances(
        db=db,
        university_id=university_id,
        student_id=student_id,
    )


@router.get("/student-stages/{university_id}/{student_clearance_id}")
def get_student_stages(
    university_id: int,
    student_clearance_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    clearance = get_student_clearance(
        db=db,
        university_id=university_id,
        clearance_id=student_clearance_id,
    )

    if not clearance:
        raise HTTPException(
            status_code=404,
            detail="Clearance not found",
        )

    if (
        student.university_id != university_id
        or clearance.student_id != student.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only access your own clearance.",
        )

    return get_clearance_stages_for_student(
        db=db,
        university_id=university_id,
        clearance_id=student_clearance_id,
    )


# ============================================================
# SUBMISSION
# ============================================================

@router.post("/submit")
def submit_clearance_route(
    payload: ClearanceSubmit,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    clearance = get_student_clearance(
        db=db,
        university_id=student.university_id,
        clearance_id=payload.clearance_id,
    )

    if not clearance:
        raise HTTPException(
            status_code=404,
            detail="Clearance not found",
        )

    if clearance.student_id != student.id:
        raise HTTPException(
            status_code=403,
            detail="You can only submit your own clearance.",
        )

    try:
        return submit_clearance(
            db=db,
            university_id=student.university_id,
            clearance_id=payload.clearance_id,
            student_id=student.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# APPROVAL / REJECTION
# ============================================================

@router.post("/approve-stage")
def approve_stage(
    payload: ClearanceStageDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return approve_clearance_stage(
            db=db,
            university_id=payload.university_id,
            clearance_id=payload.student_clearance_id,
            student_stage_id=payload.student_clearance_stage_id,
            officer_id=current_user.id,
            comment=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject-stage")
def reject_stage(
    payload: ClearanceStageReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return reject_clearance_stage(
            db=db,
            university_id=payload.university_id,
            clearance_id=payload.student_clearance_id,
            student_stage_id=payload.student_clearance_stage_id,
            officer_id=current_user.id,
            reason=payload.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# PROGRESS
# ============================================================

@router.get("/progress/{university_id}/{student_clearance_id}")
def clearance_progress(
    university_id: int,
    student_clearance_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    clearance = get_student_clearance(
        db=db,
        university_id=university_id,
        clearance_id=student_clearance_id,
    )

    if not clearance:
        raise HTTPException(
            status_code=404,
            detail="Clearance not found",
        )

    if (
        student.university_id != university_id
        or clearance.student_id != student.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only access your own clearance.",
        )

    try:
        return get_clearance_progress(
            db=db,
            university_id=university_id,
            clearance_id=student_clearance_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# FINALIZATION
# ============================================================

@router.post("/finalize")
def finalize_clearance_route(
    payload: ClearanceFinalize,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return finalize_clearance(
            db=db,
            university_id=payload.university_id,
            clearance_id=payload.student_clearance_id,
            officer_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
