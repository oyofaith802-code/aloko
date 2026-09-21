# ============================================================
# ALOKO UNIVERSITY AI
# UNIVERSITY PORTAL INTEGRATION MODELS
# ============================================================

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


# ============================================================
# UNIVERSITY PORTAL CONFIGURATION
# ============================================================

class UniversityPortalConfig(Base):
    __tablename__ = "university_portal_configs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    portal_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="api",
    )

    api_base_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    client_id: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    client_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    webhook_secret: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sso_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="inactive",
        nullable=False,
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# PORTAL SYNCHRONIZATION
# ============================================================

class UniversityPortalSync(Base):
    __tablename__ = "university_portal_syncs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_config_id: Mapped[int] = mapped_column(
        ForeignKey("university_portal_configs.id"),
        nullable=False,
        index=True,
    )

    sync_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    direction: Mapped[str] = mapped_column(
        String(30),
        default="pull",
        nullable=False,
    )

    # pending / running / completed / failed / retrying / cancelled
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    # full / incremental
    sync_mode: Mapped[str] = mapped_column(
        String(30),
        default="full",
        nullable=False,
    )

    # Pagination/checkpoint cursor for incremental synchronization
    sync_cursor: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamp of the last successfully synchronized external record
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    records_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    records_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    records_updated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    records_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Number of records where external and Aloko data conflicted
    conflicts_detected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Retry/recovery information
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


# ============================================================
# PORTAL SYNC SCHEDULE
# ============================================================

class UniversityPortalSyncSchedule(Base):
    __tablename__ = "university_portal_sync_schedules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_config_id: Mapped[int] = mapped_column(
        ForeignKey("university_portal_configs.id"),
        nullable=False,
        index=True,
    )

    sync_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # full / incremental
    sync_mode: Mapped[str] = mapped_column(
        String(30),
        default="incremental",
        nullable=False,
    )

    # interval in minutes
    interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# EXTERNAL ↔ ALOKO ID MAPPING
# ============================================================

class UniversityPortalMapping(Base):
    __tablename__ = "university_portal_mappings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_config_id: Mapped[int] = mapped_column(
        ForeignKey("university_portal_configs.id"),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    aloko_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# PORTAL WEBHOOK EVENTS
# ============================================================

class UniversityPortalWebhook(Base):
    __tablename__ = "university_portal_webhooks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_config_id: Mapped[int] = mapped_column(
        ForeignKey("university_portal_configs.id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    event_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="received",
        nullable=False,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# PORTAL INTEGRATION LOG
# ============================================================

class UniversityPortalIntegrationLog(Base):
    __tablename__ = "university_portal_integration_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_config_id: Mapped[int] = mapped_column(
        ForeignKey("university_portal_configs.id"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )