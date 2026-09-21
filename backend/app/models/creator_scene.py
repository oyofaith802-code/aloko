from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class CreatorScene(Base):
    __tablename__ = "creator_scenes"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("creator_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scene_order = Column(
        Integer,
        nullable=False,
        default=1,
    )

    script = Column(
        Text,
        nullable=True,
    )

    avatar_id = Column(
        Integer,
        ForeignKey("avatars.id"),
        nullable=True,
    )

    # Personal/custom voice reference
    voice_id = Column(
        Integer,
        ForeignKey("voices.id"),
        nullable=True,
    )

    # Built-in AI voice name
    voice = Column(
        String,
        nullable=True,
    )

    action = Column(
        String,
        nullable=True,
    )

    environment = Column(
        String,
        nullable=True,
    )

    camera = Column(
        String,
        nullable=True,
    )

    transition = Column(
        String,
        nullable=True,
    )

    captions_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    background_music = Column(
        String,
        nullable=True,
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