from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.sql import func

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    # ==========================================================
    # BASIC USER INFORMATION
    # ==========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    # Password is nullable because Google users do not use
    # a local Aloko password.
    password_hash = Column(
        String,
        nullable=True,
    )

    # ==========================================================
    # USER ROLE
    # ==========================================================

    role = Column(
        String(50),
        nullable=False,
        default="user",
        server_default="user",
        index=True,
    )

    # ==========================================================
    # EMAIL VERIFICATION
    # ==========================================================

    email_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    verification_code_hash = Column(
        String,
        nullable=True,
    )

    verification_code_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # PASSWORD RESET
    # ==========================================================

    password_reset_token_hash = Column(
        String(64),
        nullable=True,
        index=True,
    )

    password_reset_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ==========================================================
    # GOOGLE AUTHENTICATION
    # ==========================================================

    google_id = Column(
        String,
        unique=True,
        nullable=True,
        index=True,
    )

    auth_provider = Column(
        String,
        nullable=False,
        default="email",
        server_default="email",
    )

    # ==========================================================
    # ACCOUNT TIMESTAMPS
    # ==========================================================

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )