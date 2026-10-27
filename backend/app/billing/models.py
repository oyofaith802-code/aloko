from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.sql import func

from app.database.connection import Base


class AlokoSubscription(Base):
    __tablename__ = "aloko_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product = Column(String(80), nullable=False, default="customer_support")
    provider = Column(String(30), nullable=False, default="paystack")
    reference = Column(String(100), nullable=False, unique=True, index=True)
    currency = Column(String(3), nullable=False)
    amount_minor = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )



class CustomerSupportUsage(Base):
    """Persistent record of the user's one free Customer Support AI test chat."""
    __tablename__ = "customer_support_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    free_test_used = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
