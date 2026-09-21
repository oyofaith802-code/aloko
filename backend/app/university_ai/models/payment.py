from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func

from app.database.connection import Base


class UniversityPaymentConfig(Base):
    __tablename__ = "university_payment_configs"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    provider = Column(String(100), nullable=True)

    currency = Column(
        String(10),
        nullable=False,
        default="NGN",
        server_default="NGN",
    )

    merchant_name = Column(String(255), nullable=True)

    configuration_data = Column(Text, nullable=True)

    is_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class UniversityFee(Base):
    __tablename__ = "university_fees"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    name = Column(String(255), nullable=False)

    code = Column(String(100), nullable=False, index=True)

    description = Column(Text, nullable=True)

    amount = Column(Float, nullable=False)

    currency = Column(
        String(10),
        nullable=False,
        default="NGN",
        server_default="NGN",
    )

    fee_type = Column(
        String(100),
        nullable=False,
        default="general",
    )

    clearance_stage_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    is_required = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PaymentInvoice(Base):
    __tablename__ = "university_payment_invoices"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    student_id = Column(Integer, nullable=False, index=True)

    fee_id = Column(Integer, nullable=False, index=True)

    clearance_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    invoice_number = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    amount = Column(Float, nullable=False)

    currency = Column(
        String(10),
        nullable=False,
        default="NGN",
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    due_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PaymentTransaction(Base):
    __tablename__ = "university_payment_transactions"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    student_id = Column(Integer, nullable=False, index=True)

    invoice_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    provider = Column(String(100), nullable=True)

    transaction_reference = Column(
        String(255),
        nullable=True,
        index=True,
    )

    amount = Column(Float, nullable=False)

    currency = Column(
        String(10),
        nullable=False,
        default="NGN",
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    provider_response = Column(Text, nullable=True)

    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PaymentVerification(Base):
    __tablename__ = "university_payment_verifications"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    transaction_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    verified_by = Column(
        Integer,
        nullable=True,
        index=True,
    )

    verification_method = Column(
        String(50),
        nullable=False,
        default="manual",
    )

    status = Column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )

    verification_reference = Column(
        String(255),
        nullable=True,
    )

    notes = Column(Text, nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentWebhook(Base):
    __tablename__ = "university_payment_webhooks"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)

    provider = Column(String(100), nullable=False)

    event_type = Column(String(100), nullable=True)

    transaction_reference = Column(
        String(255),
        nullable=True,
        index=True,
    )

    payload = Column(Text, nullable=False)

    processing_status = Column(
        String(50),
        nullable=False,
        default="received",
        index=True,
    )

    processed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())