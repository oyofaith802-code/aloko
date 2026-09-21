from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class BusinessReport(Base):
    __tablename__ = "business_reports"

    id = Column(Integer, primary_key=True, index=True)

    workspace_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    report_type = Column(
        String(100),
        nullable=False,
        default="business_analysis",
        server_default="business_analysis",
    )

    question = Column(
        Text,
        nullable=True,
    )

    source_memory_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    content_json = Column(
        Text,
        nullable=False,
    )

    file_path = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default="ready",
        server_default="ready",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )