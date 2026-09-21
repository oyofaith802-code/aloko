from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.university_ai.models.university import University
from app.university_ai.services.university_admin_auth import (
    require_university_access,
)
from app.university_ai.services.portal_integration import (
    list_portal_configs,
    get_portal_summary,
    list_sync_jobs,
    list_sync_schedules,
    list_portal_webhooks,
    get_integration_logs,
)


def require_real_university(db: Session, university_id: int):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found.")

    if str(university.code or "").startswith("PRIVATE_LECTURER_"):
        raise HTTPException(
            status_code=403,
            detail="Private lecturer workspaces cannot use university portal integration.",
        )

    return university


router = APIRouter(
    prefix="/university/admin/portal",
    tags=["University Admin - Portal Integration"],
)


@router.get("/configs/{university_id}")
def admin_portal_configs(
    university_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return list_portal_configs(db, university_id)


@router.get("/summary/{university_id}/{portal_config_id}")
def admin_portal_summary(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return get_portal_summary(
        db,
        university_id,
        portal_config_id,
    )


@router.get("/sync/{university_id}")
def admin_sync_jobs(
    university_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return list_sync_jobs(db, university_id)


@router.get("/schedules/{university_id}")
def admin_schedules(
    university_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return list_sync_schedules(db, university_id)


@router.get("/webhooks/{university_id}")
def admin_webhooks(
    university_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return list_portal_webhooks(db, university_id)


@router.get("/logs/{university_id}")
def admin_logs(
    university_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_university_access),
):
    require_real_university(db, university_id)
    return get_integration_logs(db, university_id)
