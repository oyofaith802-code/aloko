# ============================================================
# ALOKO UNIVERSITY AI
# PORTAL INTEGRATION SERVICE
# ============================================================

from datetime import datetime, timedelta
import hashlib
import hmac
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.university_ai.services.portal_secrets import (
    decrypt_secret,
    encrypt_secret,
)

from app.university_ai.models.portal import (
    UniversityPortalConfig,
    UniversityPortalSync,
    UniversityPortalMapping,
    UniversityPortalWebhook,
    UniversityPortalIntegrationLog,
    UniversityPortalSyncSchedule,
)


# ============================================================
# VALIDATION
# ============================================================

VALID_INTEGRATION_TYPES = {
    "api",
    "sso",
    "oauth",
    "oidc",
    "webhook",
    "hybrid",
}

VALID_STATUSES = {
    "inactive",
    "active",
    "error",
    "disabled",
}

VALID_SYNC_TYPES = {
    "students",
    "lecturers",
    "faculties",
    "departments",
    "programmes",
    "courses",
    "results",
    "fees",
    "clearance",
    "all",
}

VALID_DIRECTIONS = {
    "pull",
    "push",
    "bidirectional",
}

VALID_SYNC_STATUSES = {
    "pending",
    "running",
    "completed",
    "failed",
    "cancelled",
}

VALID_SYNC_MODES = {
    "full",
    "incremental",
}

VALID_WEBHOOK_STATUSES = {
    "received",
    "processing",
    "processed",
    "failed",
}


def validate_integration_type(value: str) -> str:
    value = (value or "").strip().lower()

    if value not in VALID_INTEGRATION_TYPES:
        raise ValueError(
            f"Invalid integration type. "
            f"Allowed: {', '.join(sorted(VALID_INTEGRATION_TYPES))}"
        )

    return value


def validate_status(value: str) -> str:
    value = (value or "").strip().lower()

    if value not in VALID_STATUSES:
        raise ValueError(
            f"Invalid portal status. "
            f"Allowed: {', '.join(sorted(VALID_STATUSES))}"
        )

    return value


def validate_sync_type(value: str) -> str:
    value = (value or "").strip().lower()

    if value not in VALID_SYNC_TYPES:
        raise ValueError(
            f"Invalid sync type. "
            f"Allowed: {', '.join(sorted(VALID_SYNC_TYPES))}"
        )

    return value


def validate_sync_direction(value: str) -> str:
    value = (value or "").strip().lower()

    if value not in VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid sync direction. "
            f"Allowed: {', '.join(sorted(VALID_DIRECTIONS))}"
        )

    return value


def validate_sync_mode(value: str) -> str:
    value = (value or "full").strip().lower()

    if value not in VALID_SYNC_MODES:
        raise ValueError(
            f"Invalid sync mode. "
            f"Allowed: {', '.join(sorted(VALID_SYNC_MODES))}"
        )

    return value


# ============================================================
# SECRET MASKING
# ============================================================

def mask_secret(value: str | None) -> str | None:
    """
    Never expose complete API keys or client secrets.
    """

    if not value:
        return None

    value = str(value)

    if len(value) <= 8:
        return "*" * len(value)

    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def serialize_portal_config(
    config: UniversityPortalConfig,
) -> dict[str, Any]:

    return {
        "id": config.id,
        "university_id": config.university_id,
        "portal_name": config.portal_name,
        "portal_url": config.portal_url,
        "integration_type": config.integration_type,
        "api_base_url": config.api_base_url,

        # Never expose complete secrets.
        "api_key": mask_secret(config.api_key),
        "client_id": config.client_id,
        "client_secret": mask_secret(config.client_secret),
        "webhook_secret": mask_secret(config.webhook_secret),

        "sso_provider": config.sso_provider,
        "sync_enabled": config.sync_enabled,
        "webhook_enabled": config.webhook_enabled,
        "status": config.status,
        "last_sync_at": config.last_sync_at,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


# ============================================================
# INTEGRATION LOGGING
# ============================================================

def create_integration_log(
    db: Session,
    university_id: int,
    portal_config_id: int,
    action: str,
    status: str,
    message: str | None = None,
) -> UniversityPortalIntegrationLog:

    log = UniversityPortalIntegrationLog(
        university_id=university_id,
        portal_config_id=portal_config_id,
        action=action,
        status=status,
        message=message,
    )

    db.add(log)
    db.flush()

    return log


def get_integration_logs(
    db: Session,
    university_id: int,
    portal_config_id: int | None = None,
    limit: int = 100,
) -> list[UniversityPortalIntegrationLog]:

    stmt = select(UniversityPortalIntegrationLog).where(
        UniversityPortalIntegrationLog.university_id == university_id
    )

    if portal_config_id is not None:
        stmt = stmt.where(
            UniversityPortalIntegrationLog.portal_config_id
            == portal_config_id
        )

    stmt = stmt.order_by(
        UniversityPortalIntegrationLog.created_at.desc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


# ============================================================
# PORTAL CONFIGURATION
# ============================================================

def create_portal_config(
    db: Session,
    university_id: int,
    portal_name: str,
    portal_url: str | None = None,
    integration_type: str = "api",
    api_base_url: str | None = None,
    api_key: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    webhook_secret: str | None = None,
    sso_provider: str | None = None,
    sync_enabled: bool = False,
    webhook_enabled: bool = False,
) -> UniversityPortalConfig:

    if not portal_name or not portal_name.strip():
        raise ValueError("Portal name is required.")

    integration_type = validate_integration_type(
        integration_type
    )

    config = UniversityPortalConfig(
        university_id=university_id,
        portal_name=portal_name.strip(),
        portal_url=portal_url,
        integration_type=integration_type,
        api_base_url=api_base_url,
        api_key=encrypt_secret(api_key),
        client_id=client_id,
        client_secret=encrypt_secret(client_secret),
        webhook_secret=encrypt_secret(webhook_secret),
        sso_provider=sso_provider,
        sync_enabled=sync_enabled,
        webhook_enabled=webhook_enabled,
        status="inactive",
    )

    db.add(config)
    db.flush()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=config.id,
        action="portal_config_created",
        status="success",
        message=f"Portal configuration created for {config.portal_name}.",
    )

    db.commit()
    db.refresh(config)

    return config


def get_portal_config(
    db: Session,
    university_id: int,
    portal_config_id: int,
) -> UniversityPortalConfig | None:

    return db.scalar(
        select(UniversityPortalConfig).where(
            UniversityPortalConfig.id == portal_config_id,
            UniversityPortalConfig.university_id == university_id,
        )
    )


def list_portal_configs(
    db: Session,
    university_id: int,
) -> list[UniversityPortalConfig]:

    stmt = (
        select(UniversityPortalConfig)
        .where(
            UniversityPortalConfig.university_id == university_id
        )
        .order_by(
            UniversityPortalConfig.created_at.desc()
        )
    )

    return list(db.scalars(stmt).all())


def update_portal_config(
    db: Session,
    university_id: int,
    portal_config_id: int,
    **updates: Any,
) -> UniversityPortalConfig:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    allowed_fields = {
        "portal_name",
        "portal_url",
        "integration_type",
        "api_base_url",
        "api_key",
        "client_id",
        "client_secret",
        "webhook_secret",
        "sso_provider",
        "sync_enabled",
        "webhook_enabled",
        "status",
    }

    for field, value in updates.items():

        if field not in allowed_fields:
            continue

        if field == "integration_type":
            value = validate_integration_type(value)

        if field == "status":
            value = validate_status(value)

        if field == "portal_name" and value:
            value = value.strip()

        if field in {
            "api_key",
            "client_secret",
            "webhook_secret",
        } and value:
            value = encrypt_secret(value)

        setattr(config, field, value)

    config.updated_at = datetime.utcnow()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=config.id,
        action="portal_config_updated",
        status="success",
        message="Portal configuration updated.",
    )

    db.commit()
    db.refresh(config)

    return config


def activate_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
) -> UniversityPortalConfig:

    return update_portal_config(
        db,
        university_id,
        portal_config_id,
        status="active",
    )


def deactivate_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
) -> UniversityPortalConfig:

    return update_portal_config(
        db,
        university_id,
        portal_config_id,
        status="disabled",
        sync_enabled=False,
    )


# ============================================================
# CONNECTION VALIDATION
# ============================================================

def validate_portal_connection(
    db: Session,
    university_id: int,
    portal_config_id: int,
    timeout: int = 10,
) -> dict[str, Any]:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    if not config.api_base_url:
        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="connection_test",
            status="failed",
            message="API base URL is not configured.",
        )

        db.commit()

        return {
            "success": False,
            "message": "API base URL is not configured.",
        }

    url = config.api_base_url.rstrip("/")

    headers = {
        "Accept": "application/json",
        "User-Agent": "Aloko-University-Integration/1.0",
    }

    if config.api_key:
        headers["Authorization"] = (
            f"Bearer {decrypt_secret(config.api_key)}"
        )

    request = Request(
        url,
        headers=headers,
        method="GET",
    )

    try:

        with urlopen(request, timeout=timeout) as response:

            status_code = response.status

            success = 200 <= status_code < 300

            if success:
                config.status = "active"
            else:
                config.status = "error"

            create_integration_log(
                db=db,
                university_id=university_id,
                portal_config_id=portal_config_id,
                action="connection_test",
                status="success" if success else "failed",
                message=f"Portal returned HTTP {status_code}.",
            )

            db.commit()

            return {
                "success": success,
                "status_code": status_code,
                "message": (
                    "Portal connection successful."
                    if success
                    else "Portal returned an unsuccessful response."
                ),
            }

    except HTTPError as exc:

        config.status = "error"

        message = f"Portal returned HTTP {exc.code}."

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="connection_test",
            status="failed",
            message=message,
        )

        db.commit()

        return {
            "success": False,
            "status_code": exc.code,
            "message": message,
        }

    except URLError as exc:

        config.status = "error"

        message = f"Unable to connect to portal: {exc.reason}"

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="connection_test",
            status="failed",
            message=message,
        )

        db.commit()

        return {
            "success": False,
            "message": message,
        }

    except Exception as exc:

        config.status = "error"

        message = f"Portal connection error: {str(exc)}"

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="connection_test",
            status="failed",
            message=message,
        )

        db.commit()

        return {
            "success": False,
            "message": message,
        }


# ============================================================
# SYNC JOBS
# ============================================================

def create_sync_job(
    db: Session,
    university_id: int,
    portal_config_id: int,
    sync_type: str,
    direction: str = "pull",
    sync_mode: str = "full",
    max_retries: int = 3,
) -> UniversityPortalSync:

    sync_type = validate_sync_type(sync_type)
    direction = validate_sync_direction(direction)
    sync_mode = validate_sync_mode(sync_mode)

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    max_retries = max(0, int(max_retries))

    # Incremental sync can continue from the portal's
    # previously stored cursor.
    previous_sync = db.scalar(
        select(UniversityPortalSync)
        .where(
            UniversityPortalSync.university_id == university_id,
            UniversityPortalSync.portal_config_id == portal_config_id,
            UniversityPortalSync.sync_type == sync_type,
            UniversityPortalSync.status == "completed",
        )
        .order_by(
            UniversityPortalSync.completed_at.desc()
        )
    )

    cursor = None

    if sync_mode == "incremental" and previous_sync:
        cursor = previous_sync.sync_cursor

    sync = UniversityPortalSync(
        university_id=university_id,
        portal_config_id=portal_config_id,
        sync_type=sync_type,
        direction=direction,
        status="pending",
        sync_mode=sync_mode,
        sync_cursor=cursor,
        last_synced_at=(
            previous_sync.last_synced_at
            if previous_sync
            else None
        ),
        conflicts_detected=0,
        retry_count=0,
        max_retries=max_retries,
        next_retry_at=None,
        records_processed=0,
        records_created=0,
        records_updated=0,
        records_failed=0,
    )

    db.add(sync)
    db.flush()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_created",
        status="success",
        message=(
            f"Created {sync_type} sync job "
            f"({direction}, {sync_mode})."
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


def get_sync_job(
    db: Session,
    university_id: int,
    sync_id: int,
) -> UniversityPortalSync | None:

    return db.scalar(
        select(UniversityPortalSync).where(
            UniversityPortalSync.id == sync_id,
            UniversityPortalSync.university_id == university_id,
        )
    )


def list_sync_jobs(
    db: Session,
    university_id: int,
    portal_config_id: int | None = None,
    limit: int = 100,
) -> list[UniversityPortalSync]:

    stmt = select(UniversityPortalSync).where(
        UniversityPortalSync.university_id == university_id
    )

    if portal_config_id is not None:
        stmt = stmt.where(
            UniversityPortalSync.portal_config_id
            == portal_config_id
        )

    stmt = stmt.order_by(
        UniversityPortalSync.created_at.desc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


def start_sync_job(
    db: Session,
    university_id: int,
    sync_id: int,
) -> UniversityPortalSync:

    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise ValueError("Sync job not found.")

    if sync.status not in {"pending", "failed"}:
        raise ValueError(
            f"Sync job cannot be started from status '{sync.status}'."
        )

    # Do not retry a job beyond its configured limit.
    if (
        sync.status == "failed"
        and sync.retry_count >= sync.max_retries
    ):
        raise ValueError(
            "Sync job has reached its maximum retry limit."
        )

    sync.status = "running"
    sync.started_at = datetime.utcnow()
    sync.error_message = None
    sync.next_retry_at = None

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=sync.portal_config_id,
        action="sync_started",
        status="success",
        message=(
            f"Started {sync.sync_type} sync "
            f"({sync.sync_mode})."
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


def complete_sync_job(
    db: Session,
    university_id: int,
    sync_id: int,
    records_processed: int = 0,
    records_created: int = 0,
    records_updated: int = 0,
    records_failed: int = 0,
    sync_cursor: str | None = None,
    conflicts_detected: int = 0,
) -> UniversityPortalSync:

    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise ValueError("Sync job not found.")

    sync.status = "completed"

    sync.records_processed = max(
        0,
        records_processed,
    )

    sync.records_created = max(
        0,
        records_created,
    )

    sync.records_updated = max(
        0,
        records_updated,
    )

    sync.records_failed = max(
        0,
        records_failed,
    )

    sync.conflicts_detected = max(
        0,
        conflicts_detected,
    )

    if sync_cursor is not None:
        sync.sync_cursor = str(sync_cursor)

    now = datetime.utcnow()

    sync.completed_at = now
    sync.last_synced_at = now
    sync.next_retry_at = None
    sync.error_message = None

    config = get_portal_config(
        db,
        university_id,
        sync.portal_config_id,
    )

    if config:
        config.last_sync_at = now

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=sync.portal_config_id,
        action="sync_completed",
        status="success",
        message=(
            f"Completed {sync.sync_type} sync. "
            f"Mode: {sync.sync_mode}. "
            f"Processed: {sync.records_processed}, "
            f"created: {sync.records_created}, "
            f"updated: {sync.records_updated}, "
            f"failed: {sync.records_failed}, "
            f"conflicts: {sync.conflicts_detected}."
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


def calculate_retry_delay(
    retry_count: int,
) -> int:
    """
    Exponential backoff.

    Retry 1 -> 1 minute
    Retry 2 -> 2 minutes
    Retry 3 -> 4 minutes
    Retry 4 -> 8 minutes
    Maximum -> 60 minutes
    """

    retry_count = max(1, int(retry_count))

    delay = 2 ** (retry_count - 1)

    return min(
        delay,
        60,
    )


def fail_sync_job(
    db: Session,
    university_id: int,
    sync_id: int,
    error_message: str,
) -> UniversityPortalSync:

    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise ValueError("Sync job not found.")

    sync.status = "failed"
    sync.error_message = error_message
    sync.completed_at = datetime.utcnow()

    sync.retry_count = (
        max(0, int(sync.retry_count or 0)) + 1
    )

    if sync.retry_count <= sync.max_retries:

        delay_minutes = calculate_retry_delay(
            sync.retry_count
        )

        sync.next_retry_at = (
            datetime.utcnow()
            + timedelta(minutes=delay_minutes)
        )

        retry_message = (
            f"Retry {sync.retry_count}/{sync.max_retries} "
            f"scheduled in {delay_minutes} minute(s)."
        )

    else:

        sync.next_retry_at = None

        retry_message = (
            f"Maximum retries reached "
            f"({sync.max_retries})."
        )

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=sync.portal_config_id,
        action="sync_failed",
        status="failed",
        message=(
            f"{error_message} "
            f"{retry_message}"
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


def get_retryable_sync_jobs(
    db: Session,
    university_id: int | None = None,
    limit: int = 100,
) -> list[UniversityPortalSync]:

    now = datetime.utcnow()

    stmt = select(UniversityPortalSync).where(
        UniversityPortalSync.status == "failed",
        UniversityPortalSync.next_retry_at.is_not(None),
        UniversityPortalSync.next_retry_at <= now,
        UniversityPortalSync.retry_count
        < UniversityPortalSync.max_retries,
    )

    if university_id is not None:
        stmt = stmt.where(
            UniversityPortalSync.university_id
            == university_id
        )

    stmt = stmt.order_by(
        UniversityPortalSync.next_retry_at.asc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


def retry_sync_job(
    db: Session,
    university_id: int,
    sync_id: int,
) -> UniversityPortalSync:

    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise ValueError("Sync job not found.")

    if sync.status != "failed":
        raise ValueError(
            "Only failed sync jobs can be retried."
        )

    if sync.retry_count >= sync.max_retries:
        raise ValueError(
            "Sync job has reached its maximum retry limit."
        )

    if (
        sync.next_retry_at is not None
        and sync.next_retry_at > datetime.utcnow()
    ):
        raise ValueError(
            f"Sync retry is scheduled for "
            f"{sync.next_retry_at}."
        )

    sync.status = "pending"
    sync.error_message = None
    sync.next_retry_at = None

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=sync.portal_config_id,
        action="sync_retry_queued",
        status="success",
        message=(
            f"Retry queued for {sync.sync_type} sync. "
            f"Attempt {sync.retry_count + 1}."
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


def reset_sync_for_full_resync(
    db: Session,
    university_id: int,
    sync_id: int,
) -> UniversityPortalSync:

    sync = get_sync_job(
        db,
        university_id,
        sync_id,
    )

    if not sync:
        raise ValueError("Sync job not found.")

    if sync.status == "running":
        raise ValueError(
            "Cannot reset a running sync job."
        )

    sync.sync_mode = "full"
    sync.sync_cursor = None
    sync.last_synced_at = None
    sync.conflicts_detected = 0
    sync.retry_count = 0
    sync.next_retry_at = None
    sync.error_message = None
    sync.status = "pending"

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=sync.portal_config_id,
        action="sync_reset",
        status="success",
        message=(
            f"Reset {sync.sync_type} sync for full resynchronization."
        ),
    )

    db.commit()
    db.refresh(sync)

    return sync


# ============================================================
# SYNC SCHEDULES
# ============================================================

def create_sync_schedule(
    db: Session,
    university_id: int,
    portal_config_id: int,
    sync_type: str,
    interval_minutes: int,
    sync_mode: str = "incremental",
    enabled: bool = True,
) -> UniversityPortalSyncSchedule:

    sync_type = validate_sync_type(sync_type)
    sync_mode = validate_sync_mode(sync_mode)

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    interval_minutes = max(
        1,
        int(interval_minutes),
    )

    now = datetime.utcnow()

    schedule = UniversityPortalSyncSchedule(
        university_id=university_id,
        portal_config_id=portal_config_id,
        sync_type=sync_type,
        sync_mode=sync_mode,
        interval_minutes=interval_minutes,
        enabled=enabled,
        next_run_at=now + timedelta(
            minutes=interval_minutes
        ),
        last_run_at=None,
        last_status=None,
    )

    db.add(schedule)
    db.flush()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_schedule_created",
        status="success",
        message=(
            f"Created {sync_type} {sync_mode} schedule "
            f"every {interval_minutes} minute(s)."
        ),
    )

    db.commit()
    db.refresh(schedule)

    return schedule


def get_sync_schedule(
    db: Session,
    university_id: int,
    schedule_id: int,
) -> UniversityPortalSyncSchedule | None:

    return db.scalar(
        select(UniversityPortalSyncSchedule).where(
            UniversityPortalSyncSchedule.id == schedule_id,
            UniversityPortalSyncSchedule.university_id
            == university_id,
        )
    )


def list_sync_schedules(
    db: Session,
    university_id: int,
    portal_config_id: int | None = None,
    enabled_only: bool = False,
    limit: int = 100,
) -> list[UniversityPortalSyncSchedule]:

    stmt = select(UniversityPortalSyncSchedule).where(
        UniversityPortalSyncSchedule.university_id
        == university_id
    )

    if portal_config_id is not None:
        stmt = stmt.where(
            UniversityPortalSyncSchedule.portal_config_id
            == portal_config_id
        )

    if enabled_only:
        stmt = stmt.where(
            UniversityPortalSyncSchedule.enabled.is_(True)
        )

    stmt = stmt.order_by(
        UniversityPortalSyncSchedule.next_run_at.asc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


def get_due_sync_schedules(
    db: Session,
    university_id: int | None = None,
    limit: int = 100,
) -> list[UniversityPortalSyncSchedule]:

    now = datetime.utcnow()

    stmt = select(UniversityPortalSyncSchedule).where(
        UniversityPortalSyncSchedule.enabled.is_(True),
        UniversityPortalSyncSchedule.next_run_at.is_not(None),
        UniversityPortalSyncSchedule.next_run_at <= now,
    )

    if university_id is not None:
        stmt = stmt.where(
            UniversityPortalSyncSchedule.university_id
            == university_id
        )

    stmt = stmt.order_by(
        UniversityPortalSyncSchedule.next_run_at.asc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


def update_sync_schedule(
    db: Session,
    university_id: int,
    schedule_id: int,
    **updates: Any,
) -> UniversityPortalSyncSchedule:

    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise ValueError("Sync schedule not found.")

    allowed_fields = {
        "sync_type",
        "sync_mode",
        "interval_minutes",
        "enabled",
        "next_run_at",
    }

    for field, value in updates.items():

        if field not in allowed_fields:
            continue

        if field == "sync_type":
            value = validate_sync_type(value)

        if field == "sync_mode":
            value = validate_sync_mode(value)

        if field == "interval_minutes":
            value = max(1, int(value))

        setattr(
            schedule,
            field,
            value,
        )

    schedule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(schedule)

    return schedule


def disable_sync_schedule(
    db: Session,
    university_id: int,
    schedule_id: int,
) -> UniversityPortalSyncSchedule:

    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise ValueError("Sync schedule not found.")

    schedule.enabled = False
    schedule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(schedule)

    return schedule


def enable_sync_schedule(
    db: Session,
    university_id: int,
    schedule_id: int,
) -> UniversityPortalSyncSchedule:

    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise ValueError("Sync schedule not found.")

    schedule.enabled = True

    if not schedule.next_run_at:
        schedule.next_run_at = (
            datetime.utcnow()
            + timedelta(
                minutes=schedule.interval_minutes
            )
        )

    schedule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(schedule)

    return schedule


def mark_schedule_run(
    db: Session,
    university_id: int,
    schedule_id: int,
    status: str,
) -> UniversityPortalSyncSchedule:

    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise ValueError("Sync schedule not found.")

    now = datetime.utcnow()

    schedule.last_run_at = now
    schedule.last_status = status

    if schedule.enabled:
        schedule.next_run_at = (
            now
            + timedelta(
                minutes=max(
                    1,
                    int(schedule.interval_minutes),
                )
            )
        )
    else:
        schedule.next_run_at = None

    schedule.updated_at = now

    db.commit()
    db.refresh(schedule)

    return schedule


def create_sync_job_from_schedule(
    db: Session,
    university_id: int,
    schedule_id: int,
) -> UniversityPortalSync:

    schedule = get_sync_schedule(
        db,
        university_id,
        schedule_id,
    )

    if not schedule:
        raise ValueError("Sync schedule not found.")

    if not schedule.enabled:
        raise ValueError("Sync schedule is disabled.")

    sync = create_sync_job(
        db=db,
        university_id=university_id,
        portal_config_id=schedule.portal_config_id,
        sync_type=schedule.sync_type,
        direction="pull",
        sync_mode=schedule.sync_mode,
    )

    mark_schedule_run(
        db=db,
        university_id=university_id,
        schedule_id=schedule.id,
        status="queued",
    )

    return sync


# ============================================================
# EXTERNAL ↔ ALOKO MAPPINGS
# ============================================================

def create_portal_mapping(
    db: Session,
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    aloko_id: int,
    external_id: str,
    external_reference: str | None = None,
) -> UniversityPortalMapping:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    if not entity_type:
        raise ValueError("Entity type is required.")

    if not external_id:
        raise ValueError("External ID is required.")

    existing = db.scalar(
        select(UniversityPortalMapping).where(
            UniversityPortalMapping.university_id
            == university_id,
            UniversityPortalMapping.portal_config_id
            == portal_config_id,
            UniversityPortalMapping.entity_type
            == entity_type,
            UniversityPortalMapping.external_id
            == external_id,
        )
    )

    if existing:
        existing.aloko_id = aloko_id
        existing.external_reference = external_reference
        existing.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)

        return existing

    mapping = UniversityPortalMapping(
        university_id=university_id,
        portal_config_id=portal_config_id,
        entity_type=entity_type,
        aloko_id=aloko_id,
        external_id=external_id,
        external_reference=external_reference,
    )

    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return mapping


def get_portal_mapping(
    db: Session,
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    external_id: str,
) -> UniversityPortalMapping | None:

    return db.scalar(
        select(UniversityPortalMapping).where(
            UniversityPortalMapping.university_id
            == university_id,
            UniversityPortalMapping.portal_config_id
            == portal_config_id,
            UniversityPortalMapping.entity_type
            == entity_type,
            UniversityPortalMapping.external_id
            == external_id,
        )
    )


def get_mapping_by_aloko_id(
    db: Session,
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    aloko_id: int,
) -> UniversityPortalMapping | None:

    return db.scalar(
        select(UniversityPortalMapping).where(
            UniversityPortalMapping.university_id
            == university_id,
            UniversityPortalMapping.portal_config_id
            == portal_config_id,
            UniversityPortalMapping.entity_type
            == entity_type,
            UniversityPortalMapping.aloko_id
            == aloko_id,
        )
    )


def list_portal_mappings(
    db: Session,
    university_id: int,
    portal_config_id: int,
    entity_type: str | None = None,
) -> list[UniversityPortalMapping]:

    stmt = select(UniversityPortalMapping).where(
        UniversityPortalMapping.university_id
        == university_id,
        UniversityPortalMapping.portal_config_id
        == portal_config_id,
    )

    if entity_type:
        stmt = stmt.where(
            UniversityPortalMapping.entity_type
            == entity_type
        )

    stmt = stmt.order_by(
        UniversityPortalMapping.created_at.desc()
    )

    return list(db.scalars(stmt).all())


# ============================================================
# WEBHOOKS
# ============================================================

def record_portal_webhook(
    db: Session,
    university_id: int,
    portal_config_id: int,
    event_type: str,
    payload: dict[str, Any] | str,
    event_reference: str | None = None,
) -> UniversityPortalWebhook:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    if event_reference:

        existing = db.execute(
            select(UniversityPortalWebhook).where(
                UniversityPortalWebhook.university_id
                == university_id,
                UniversityPortalWebhook.portal_config_id
                == portal_config_id,
                UniversityPortalWebhook.event_reference
                == event_reference,
            )
        ).scalars().first()

        if existing:
            return existing

    if isinstance(payload, dict):
        payload_text = json.dumps(
            payload,
            ensure_ascii=False,
        )
    else:
        payload_text = str(payload)

    webhook = UniversityPortalWebhook(
        university_id=university_id,
        portal_config_id=portal_config_id,
        event_type=event_type,
        event_reference=event_reference,
        payload=payload_text,
        status="received",
    )

    db.add(webhook)
    db.flush()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="webhook_received",
        status="success",
        message=f"Webhook received: {event_type}.",
    )

    db.commit()
    db.refresh(webhook)

    return webhook


def get_portal_webhook(
    db: Session,
    university_id: int,
    webhook_id: int,
) -> UniversityPortalWebhook | None:

    return db.scalar(
        select(UniversityPortalWebhook).where(
            UniversityPortalWebhook.id == webhook_id,
            UniversityPortalWebhook.university_id
            == university_id,
        )
    )


def list_portal_webhooks(
    db: Session,
    university_id: int,
    portal_config_id: int | None = None,
    limit: int = 100,
) -> list[UniversityPortalWebhook]:

    stmt = select(UniversityPortalWebhook).where(
        UniversityPortalWebhook.university_id
        == university_id
    )

    if portal_config_id is not None:
        stmt = stmt.where(
            UniversityPortalWebhook.portal_config_id
            == portal_config_id
        )

    stmt = stmt.order_by(
        UniversityPortalWebhook.created_at.desc()
    ).limit(limit)

    return list(db.scalars(stmt).all())


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify an incoming portal webhook using HMAC-SHA256.
    """

    if not payload or not signature or not secret:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature.strip()

    if provided.startswith("sha256="):
        provided = provided[7:]

    return hmac.compare_digest(
        expected,
        provided,
    )


def process_portal_webhook(
    db: Session,
    university_id: int,
    webhook_id: int,
) -> UniversityPortalWebhook:

    webhook = get_portal_webhook(
        db,
        university_id,
        webhook_id,
    )

    if not webhook:
        raise ValueError("Webhook not found.")

    if webhook.status == "processed":
        return webhook

    webhook.status = "processing"

    try:

        payload = json.loads(webhook.payload)

        # ----------------------------------------------------
        # Foundation only.
        #
        # Actual event-specific synchronization is handled
        # by the dedicated sync engines.
        # ----------------------------------------------------

        webhook.status = "processed"
        webhook.processed_at = datetime.utcnow()

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=webhook.portal_config_id,
            action="webhook_processed",
            status="success",
            message=(
                f"Processed webhook {webhook.event_type}. "
                f"Payload keys: {list(payload.keys())}"
            ),
        )

    except Exception as exc:

        webhook.status = "failed"

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=webhook.portal_config_id,
            action="webhook_processing",
            status="failed",
            message=str(exc),
        )

    db.commit()
    db.refresh(webhook)

    return webhook


# ============================================================
# PORTAL SUMMARY
# ============================================================

def get_portal_summary(
    db: Session,
    university_id: int,
    portal_config_id: int,
) -> dict[str, Any]:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not config:
        raise ValueError("Portal configuration not found.")

    syncs = list_sync_jobs(
        db,
        university_id,
        portal_config_id,
        limit=1000,
    )

    mappings = list_portal_mappings(
        db,
        university_id,
        portal_config_id,
    )

    webhooks = list_portal_webhooks(
        db,
        university_id,
        portal_config_id,
        limit=1000,
    )

    schedules = list_sync_schedules(
        db,
        university_id,
        portal_config_id,
        limit=1000,
    )

    logs = get_integration_logs(
        db,
        university_id,
        portal_config_id,
        limit=20,
    )

    return {
        "portal": serialize_portal_config(config),

        "syncs": {
            "total": len(syncs),

            "pending": sum(
                1 for item in syncs
                if item.status == "pending"
            ),

            "running": sum(
                1 for item in syncs
                if item.status == "running"
            ),

            "completed": sum(
                1 for item in syncs
                if item.status == "completed"
            ),

            "failed": sum(
                1 for item in syncs
                if item.status == "failed"
            ),

            "retryable": sum(
                1
                for item in syncs
                if (
                    item.status == "failed"
                    and item.next_retry_at is not None
                    and item.retry_count < item.max_retries
                )
            ),

            "conflicts": sum(
                max(
                    0,
                    int(item.conflicts_detected or 0),
                )
                for item in syncs
            ),
        },

        "schedules": {
            "total": len(schedules),

            "enabled": sum(
                1
                for item in schedules
                if item.enabled
            ),

            "disabled": sum(
                1
                for item in schedules
                if not item.enabled
            ),
        },

        "mappings": {
            "total": len(mappings),
        },

        "webhooks": {
            "total": len(webhooks),

            "received": sum(
                1
                for item in webhooks
                if item.status == "received"
            ),

            "processed": sum(
                1
                for item in webhooks
                if item.status == "processed"
            ),

            "failed": sum(
                1
                for item in webhooks
                if item.status == "failed"
            ),
        },

        "recent_logs": [
            {
                "id": log.id,
                "action": log.action,
                "status": log.status,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }