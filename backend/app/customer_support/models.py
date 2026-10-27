from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class SupportWorkspace(Base):
    __tablename__ = "support_workspaces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False, default="other")
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SupportKnowledgeItem(Base):
    __tablename__ = "support_knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer,
        ForeignKey("support_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SupportConversation(Base):
    __tablename__ = "support_conversations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer,
        ForeignKey("support_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_identifier = Column(String(255), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    channel = Column(String(40), nullable=False, default="web_test")
    status = Column(String(40), nullable=False, default="open", index=True)
    human_requested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("support_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
