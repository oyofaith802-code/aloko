from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Text,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class BusinessMemory(Base):
    __tablename__ = "business_memories"

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

    question = Column(
        Text,
        nullable=False,
    )

    sql_query = Column(
        Text,
        nullable=True,
    )

    result_summary = Column(
        Text,
        nullable=True,
    )

    ai_answer = Column(
        Text,
        nullable=True,
    )

    chart_type = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )