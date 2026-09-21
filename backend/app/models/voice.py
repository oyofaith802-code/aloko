from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Voice(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    voice_type = Column(
        String,
        nullable=False,
        default="custom",
    )

    # Local uploaded reference audio
    audio_url = Column(
        String,
        nullable=True,
    )

    # ID returned by the voice-cloning provider
    provider_voice_id = Column(
        String,
        nullable=True,
        index=True,
    )

    # pending / processing / ready / failed
    status = Column(
        String,
        nullable=False,
        default="pending",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )