from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    BigInteger,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class BusinessDataset(Base):
    __tablename__ = "business_datasets"

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

    name = Column(
        String(255),
        nullable=False,
    )

    original_filename = Column(
        String(500),
        nullable=True,
    )

    source_type = Column(
        String(50),
        nullable=False,
    )

    storage_path = Column(
        Text,
        nullable=True,
    )

    table_name = Column(
        String(255),
        nullable=True,
    )

    row_count = Column(
        BigInteger,
        nullable=True,
    )

    schema_json = Column(
        Text,
        nullable=True,
    )

    profile_json = Column(
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