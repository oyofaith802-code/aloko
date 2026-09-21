# ============================================================
# ALOKO UNIVERSITY AI
# UNIVERSITY PORTAL INTEGRATION ROUTES
# Phase 8.6.8 - Production Synchronization & Recovery
# ============================================================

import os
import hmac
import hashlib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User

from app.university_ai.services.university_admin_auth import (
    require_university_admin,
    require_university_access,
)

from app.university_ai.services.portal_secrets import decrypt_secret
from app.university_ai.services.portal_integration import (
    verify_webhook_signature,
    activate_portal,
    complete_sync_job,
    create_portal_config,
    create_portal_mapping,
    create_sync_job,
    create_sync_job_from_schedule,
    create_sync_schedule,
    deactivate_portal,
    disable_sync_schedule,
    enable_sync_schedule,
    fail_sync_job,
    get_due_sync_schedules,
    get_integration_logs,
    get_mapping_by_aloko_id,
    get_portal_config,
    get_portal_mapping,
    get_portal_summary,
    get_sync_job,
    get_sync_schedule,
    get_retryable_sync_jobs,
    list_portal_configs,
    list_portal_mappings,
    list_portal_webhooks,
    list_sync_jobs,
    list_sync_schedules,
    process_portal_webhook,
    record_portal_webhook,
    reset_sync_for_full_resync,
    retry_sync_job,
    serialize_portal_config,
    start_sync_job,
    update_portal_config,
    update_sync_schedule,
    validate_portal_connection,
)

from app.university_ai.services.fee_portal_sync import (
    sync_fees_from_portal,
)

from app.university_ai.services.clearance_portal_sync import (
    sync_clearance_from_portal,
)

from app.university_ai.services.student_portal_sync import (
    sync_students_from_portal,
)

from app.university_ai.services.lecturer_portal_sync import (
    sync_lecturers_from_portal,
)

from app.university_ai.services.course_portal_sync import (
    sync_courses_from_portal,
)

from app.university_ai.services.result_portal_sync import (
    sync_results_from_portal,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/university/portal",
    tags=["University Portal Integration"],
)


# ============================================================
# PORTAL API KEY AUTHENTICATION
# ============================================================

portal_api_key_header = APIKeyHeader(
    name="X-Aloko-Portal-Key",
    auto_error=False,
)


def require_portal_api_key(
    api_key: str | None = Depends(portal_api_key_header),
):
    """
    Authenticate protected portal integration operations.

    The actual API key is never stored in the application.
    Only its SHA-256 hash is stored in:

        ALOKO_PORTAL_API_KEY_HASH
    """

    expected_hash = os.getenv("ALOKO_PORTAL_API_KEY_HASH")

    if not expected_hash:
        raise HTTPException(
            status_code=503,
            detail="Portal API authentication is not configured.",
        )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Portal API key is required.",
        )

    provided_hash = hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()

    if not hmac.compare_digest(
        provided_hash,
        expected_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid portal API key.",
        )

    return True


# ============================================================
# REQUEST MODELS
# ============================================================

class PortalCreateRequest(BaseModel):
    university_id: int
    portal_name: str = Field(min_length=1)
    portal_url: str | None = None
    integration_type: str = "api"
    api_base_url: str | None = None
    api_key: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    webhook_secret: str | None = None
    sso_provider: str | None = None
    sync_enabled: bool = False
    webhook_enabled: bool = False


class PortalUpdateRequest(BaseModel):
    university_id: int
    portal_name: str | None = None
    portal_url: str | None = None
    integration_type: str | None = None
    api_base_url: str | None = None
    api_key: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    webhook_secret: str | None = None
    sso_provider: str | None = None
    sync_enabled: bool | None = None
    webhook_enabled: bool | None = None
    status: str | None = None


class SyncCreateRequest(BaseModel):
    university_id: int
    portal_config_id: int
    sync_type: str
    direction: str = "pull"
    sync_mode: str = "full"
    max_retries: int = Field(default=3, ge=0, le=20)


class SyncCompleteRequest(BaseModel):
    university_id: int
    records_processed: int = Field(default=0, ge=0)
    records_created: int = Field(default=0, ge=0)
    records_updated: int = Field(default=0, ge=0)
    records_failed: int = Field(default=0, ge=0)
    sync_cursor: str | None = None
    conflicts_detected: int = Field(default=0, ge=0)


class SyncFailRequest(BaseModel):
    university_id: int
    error_message: str = Field(min_length=1)


class MappingCreateRequest(BaseModel):
    university_id: int
    portal_config_id: int
    entity_type: str
    aloko_id: int
    external_id: str
    external_reference: str | None = None


class WebhookCreateRequest(BaseModel):
    university_id: int
    portal_config_id: int
    event_type: str
    event_reference: str | None = None
    payload: dict[str, Any]


class ScheduleCreateRequest(BaseModel):
    university_id: int
    portal_config_id: int
    sync_type: str
    interval_minutes: int = Field(
        default=60,
        ge=1,
    )
    sync_mode: str = "incremental"
    enabled: bool = True


class ScheduleUpdateRequest(BaseModel):
    university_id: int
    sync_type: str | None = None
    sync_mode: str | None = None
    interval_minutes: int | None = Field(
        default=None,
        ge=1,
    )
    enabled: bool | None = None


# ============================================================
# PORTAL CONFIGURATION
# ============================================================

@router.post("/configs")
def create_portal(
    request: PortalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        portal = create_portal_config(
            db=db,
            university_id=request.university_id,
            portal_name=request.portal_name,
            portal_url=request.portal_url,
            integration_type=request.integration_type,
            api_base_url=request.api_base_url,
            api_key=request.api_key,
            client_id=request.client_id,
            client_secret=request.client_secret,
            webhook_secret=request.webhook_secret,
            sso_provider=request.sso_provider,
            sync_enabled=request.sync_enabled,
            webhook_enabled=request.webhook_enabled,
        )

        db.commit()
        db.refresh(portal)

        return serialize_portal_config(portal)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/configs/{university_id}")
def get_portals(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return [
        serialize_portal_config(portal)
        for portal in list_portal_configs(
            db,
            university_id,
        )
    ]


@router.get("/configs/{university_id}/{portal_config_id}")
def get_portal(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    portal = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not portal:
        raise HTTPException(
            status_code=404,
            detail="Portal configuration not found.",
        )

    return serialize_portal_config(portal)


@router.patch("/configs/{portal_config_id}")
def update_portal(
    portal_config_id: int,
    request: PortalUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        portal = update_portal_config(
            db=db,
            university_id=request.university_id,
            portal_config_id=portal_config_id,
            portal_name=request.portal_name,
            portal_url=request.portal_url,
            integration_type=request.integration_type,
            api_base_url=request.api_base_url,
            api_key=request.api_key,
            client_id=request.client_id,
            client_secret=request.client_secret,
            webhook_secret=request.webhook_secret,
            sso_provider=request.sso_provider,
            sync_enabled=request.sync_enabled,
            webhook_enabled=request.webhook_enabled,
            status=request.status,
        )

        if not portal:
            raise HTTPException(
                status_code=404,
                detail="Portal configuration not found.",
            )

        db.commit()
        db.refresh(portal)

        return serialize_portal_config(portal)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/configs/{university_id}/{portal_config_id}/activate"
)
def activate_portal_route(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        portal = activate_portal(
            db,
            university_id,
            portal_config_id,
        )

        db.commit()

        return serialize_portal_config(portal)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/configs/{university_id}/{portal_config_id}/deactivate"
)
def deactivate_portal_route(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        portal = deactivate_portal(
            db,
            university_id,
            portal_config_id,
        )

        db.commit()

        return serialize_portal_config(portal)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# CONNECTION TEST
# ============================================================

@router.post(
    "/configs/{university_id}/{portal_config_id}/test"
)
def test_portal_connection(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        return validate_portal_connection(
            db,
            university_id,
            portal_config_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Portal connection test failed: {exc}",
        )


# ============================================================
# SYNC JOBS
# ============================================================

@router.post("/sync")
def create_sync(
    request: SyncCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = create_sync_job(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            sync_type=request.sync_type,
            direction=request.direction,
            sync_mode=request.sync_mode,
            max_retries=request.max_retries,
        )

        db.commit()
        db.refresh(sync)

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/sync/{university_id}")
def get_syncs(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return list_sync_jobs(
        db,
        university_id,
    )


@router.get("/sync/{university_id}/retryable")
def get_retryable_syncs(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return get_retryable_sync_jobs(
        db,
        university_id,
    )


@router.get("/sync/{university_id}/{sync_id}")
def get_sync(
    university_id: int,
    sync_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise HTTPException(
            status_code=404,
            detail="Sync job not found.",
        )

    return sync


@router.post("/sync/{university_id}/{sync_id}/start")
def start_sync(
    university_id: int,
    sync_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = start_sync_job(
            db,
            university_id,
            sync_id,
        )

        db.commit()

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/sync/{sync_id}/complete")
def complete_sync(
    sync_id: int,
    request: SyncCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = complete_sync_job(
            db=db,
            university_id=request.university_id,
            sync_id=sync_id,
            records_processed=request.records_processed,
            records_created=request.records_created,
            records_updated=request.records_updated,
            records_failed=request.records_failed,
            sync_cursor=request.sync_cursor,
            conflicts_detected=request.conflicts_detected,
        )

        db.commit()

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/sync/{sync_id}/fail")
def fail_sync(
    sync_id: int,
    request: SyncFailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = fail_sync_job(
            db=db,
            university_id=request.university_id,
            sync_id=sync_id,
            error_message=request.error_message,
        )

        db.commit()

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# SYNC RETRY
# ============================================================

@router.post(
    "/sync/{university_id}/{sync_id}/retry"
)
def retry_sync(
    university_id: int,
    sync_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = retry_sync_job(
            db,
            university_id,
            sync_id,
        )

        db.commit()

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# FULL RESYNC RESET
# ============================================================

@router.post(
    "/sync/{university_id}/{sync_id}/reset"
)
def reset_sync(
    university_id: int,
    sync_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = reset_sync_for_full_resync(
            db,
            university_id,
            sync_id,
        )

        db.commit()

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# SYNC SCHEDULES
# ============================================================

@router.post("/schedules")
def create_schedule(
    request: ScheduleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        schedule = create_sync_schedule(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            sync_type=request.sync_type,
            interval_minutes=request.interval_minutes,
            sync_mode=request.sync_mode,
            enabled=request.enabled,
        )

        db.commit()
        db.refresh(schedule)

        return schedule

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/schedules/{university_id}")
def get_schedules(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return list_sync_schedules(
        db,
        university_id,
    )


@router.get(
    "/schedules/{university_id}/due"
)
def get_due_schedules(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return get_due_sync_schedules(
        db,
        university_id,
    )


@router.get(
    "/schedules/{university_id}/{schedule_id}"
)
def get_schedule(
    university_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Sync schedule not found.",
        )

    return schedule


@router.patch(
    "/schedules/{university_id}/{schedule_id}"
)
def update_schedule(
    university_id: int,
    schedule_id: int,
    request: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        schedule = update_sync_schedule(
            db=db,
            university_id=university_id,
            schedule_id=schedule_id,
            sync_type=request.sync_type,
            sync_mode=request.sync_mode,
            interval_minutes=request.interval_minutes,
            enabled=request.enabled,
        )

        return schedule

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/schedules/{university_id}/{schedule_id}/enable"
)
def enable_schedule(
    university_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        schedule = enable_sync_schedule(
            db,
            university_id,
            schedule_id,
        )

        return schedule

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/schedules/{university_id}/{schedule_id}/disable"
)
def disable_schedule(
    university_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        schedule = disable_sync_schedule(
            db,
            university_id,
            schedule_id,
        )

        return schedule

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/schedules/{university_id}/{schedule_id}/run"
)
def run_schedule(
    university_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        sync = create_sync_job_from_schedule(
            db,
            university_id,
            schedule_id,
        )

        return sync

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# MAPPINGS
# ============================================================

@router.post("/mappings")
def create_mapping(
    request: MappingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=request.university_id,
        db=db,
        current_user=current_user,
    )
    try:
        mapping = create_portal_mapping(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            entity_type=request.entity_type,
            aloko_id=request.aloko_id,
            external_id=request.external_id,
            external_reference=request.external_reference,
        )

        db.commit()
        db.refresh(mapping)

        return mapping

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/mappings/{university_id}/{portal_config_id}"
)
def get_mappings(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return list_portal_mappings(
        db,
        university_id,
        portal_config_id,
    )


@router.get(
    "/mappings/{university_id}/{portal_config_id}/{entity_type}/{external_id}"
)
def get_mapping(
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    external_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    mapping = get_portal_mapping(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        entity_type=entity_type,
        external_id=external_id,
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Portal mapping not found.",
        )

    return mapping


@router.get(
    "/mappings/{university_id}/{portal_config_id}/aloko/{entity_type}/{aloko_id}"
)
def get_aloko_mapping(
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    aloko_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    mapping = get_mapping_by_aloko_id(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        entity_type=entity_type,
        aloko_id=aloko_id,
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Portal mapping not found.",
        )

    return mapping


# ============================================================
# WEBHOOKS
# IMPORTANT:
# Webhooks use HMAC signature authentication.
# DO NOT attach require_portal_api_key here.
# ============================================================

@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        raw_body = await request.body()

        signature = request.headers.get(
            "X-Webhook-Signature"
        )

        if not signature:
            raise HTTPException(
                status_code=401,
                detail="Webhook signature is required.",
            )

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON payload.",
            )

        university_id = body.get("university_id")
        portal_config_id = body.get("portal_config_id")
        event_type = body.get("event_type")
        event_reference = body.get("event_reference")
        payload = body.get("payload")

        if (
            not university_id
            or not portal_config_id
            or not event_type
            or payload is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Missing required webhook fields.",
            )

        portal = get_portal_config(
            db,
            university_id,
            portal_config_id,
        )

        if not portal:
            raise HTTPException(
                status_code=404,
                detail="Portal configuration not found.",
            )

        if portal.status != "active":
            raise HTTPException(
                status_code=403,
                detail="Portal is not active.",
            )

        if not portal.webhook_enabled:
            raise HTTPException(
                status_code=403,
                detail="Webhooks are disabled for this portal.",
            )

        webhook_secret = decrypt_secret(
            portal.webhook_secret
        )

        if not webhook_secret:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Webhook secret is not configured "
                    "for this portal."
                ),
            )

        if not verify_webhook_signature(
            raw_body,
            signature,
            webhook_secret,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature.",
            )

        webhook = record_portal_webhook(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            event_type=event_type,
            event_reference=event_reference,
            payload=payload,
        )

        db.commit()
        db.refresh(webhook)

        return webhook

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/webhooks/{university_id}")
def get_webhooks(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return list_portal_webhooks(
        db,
        university_id,
    )


@router.post(
    "/webhooks/{university_id}/{webhook_id}/process"
)
def process_webhook(
    university_id: int,
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    try:
        return process_portal_webhook(
            db,
            university_id,
            webhook_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# LOGS
# ============================================================

@router.get("/logs/{university_id}")
def get_logs(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return get_integration_logs(
        db,
        university_id,
    )


# ============================================================
# SUMMARY
# ============================================================

@router.get(
    "/summary/{university_id}/{portal_config_id}"
)
def portal_summary(
    university_id: int,
    portal_config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )
    return get_portal_summary(
        db,
        university_id,
        portal_config_id,
    )


# ============================================================
# STUDENT PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class StudentSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/students"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/students")
def sync_students(
    request: StudentSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_students_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Student portal sync failed: {exc}",
        )


# ============================================================
# LECTURER PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class LecturerSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/lecturers"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/lecturers")
def sync_lecturers(
    request: LecturerSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_lecturers_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Lecturer portal sync failed: {exc}",
        )


# ============================================================
# COURSE PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class CourseSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/courses"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/courses")
def sync_courses(
    request: CourseSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_courses_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Course portal sync failed: {exc}",
        )


# ============================================================
# RESULTS PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class ResultSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/results"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/results")
def sync_results(
    request: ResultSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_results_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Result portal sync failed: {exc}",
        )


# ============================================================
# FEE PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class FeeSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/fees"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/fees")
def sync_fees(
    request: FeeSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_fees_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Fee portal sync failed: {exc}",
        )


# ============================================================
# CLEARANCE PORTAL SYNC
# PROTECTED BY PORTAL API KEY
# ============================================================

class ClearanceSyncRequest(BaseModel):
    university_id: int
    portal_config_id: int
    endpoint: str = "/clearance"
    page_size: int = Field(default=100, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1)


@router.post("/sync/clearance")
def sync_clearance(
    request: ClearanceSyncRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_portal_api_key),
):
    try:
        return sync_clearance_from_portal(
            db=db,
            university_id=request.university_id,
            portal_config_id=request.portal_config_id,
            endpoint=request.endpoint,
            page_size=request.page_size,
            max_pages=request.max_pages,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Clearance portal sync failed: {exc}",
        )
