from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class UniversityPortalConfig(Base):
    __tablename__ = "university_portal_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )

    portal_name: Mapped[str] = mapped_column(String(255), nullable=False)

    portal_url: Mapped[str | None] = mapped_column(String(1000))

    integration_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="api",
    )

    api_base_url: Mapped[str | None] = mapped_column(String(1000))

    api_key: Mapped[str | None] = mapped_column(Text)

    client_id: Mapped[str | None] = mapped_column(String(500))

    client_secret: Mapped[str | None] = mapped_column(Text)

    sso_provider: Mapped[str | None] = mapped_column(String(100))

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

    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime)

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


class UniversityPortalSync(Base):
    __tablename__ = "university_portal_syncs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
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

    error_message: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class UniversityPortalMapping(Base):
    __tablename__ = "university_portal_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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


class UniversityPortalWebhook(Base):
    __tablename__ = "university_portal_webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class UniversityPortalIntegrationLog(Base):
    __tablename__ = "university_portal_integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )