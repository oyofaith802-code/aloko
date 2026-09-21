from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func


from app.database.connection import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)
    script = Column(String, nullable=False)
    video_url = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())