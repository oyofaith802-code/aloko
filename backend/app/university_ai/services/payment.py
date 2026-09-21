import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.university_ai.models.payment import (
    UniversityPaymentConfig,
    UniversityFee,
    PaymentInvoice,
    PaymentTransaction,
    PaymentVerification,
    PaymentWebhook,
)


VALID_INVOICE_STATUSES = {
    "pending",
    "paid",
    "cancelled",
    "expired",
}

VALID_TRANSACTION_STATUSES = {
    "pending",
    "successful",
    "failed",
    "cancelled",
}

VALID_VERIFICATION_STATUSES = {
    "pending",
    "verified",
    "rejected",
}


def _now():
    return datetime.now(timezone.utc)


# ============================================================
# PAYMENT CONFIGURATION
# ============================================================

def create_payment_config(
    db: Session,
    university_id: int,
    provider: str | None = None,
    currency: str = "NGN",
    merchant_name: str | None = None,
    configuration_data: dict | None = None,
    is_enabled: bool = False,
):
    existing = (
        db.query(UniversityPaymentConfig)
        .filter(
            UniversityPaymentConfig.university_id == university_id
        )
        .first()
    )

    if existing:
        raise ValueError(
            "Payment configuration already exists"
        )

    config = UniversityPaymentConfig(
        university_id=university_id,
        provider=provider,
        currency=currency.upper(),
        merchant_name=merchant_name,
        configuration_data=(
            json.dumps(configuration_data)
            if configuration_data
            else None
        ),
        is_enabled=is_enabled,
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def get_payment_config(
    db: Session,
    university_id: int,
):
    return (
        db.query(UniversityPaymentConfig)
        .filter(
            UniversityPaymentConfig.university_id == university_id
        )
        .first()
    )


def update_payment_config(
    db: Session,
    university_id: int,
    provider: str | None = None,
    currency: str | None = None,
    merchant_name: str | None = None,
    configuration_data: dict | None = None,
    is_enabled: bool | None = None,
):
    config = get_payment_config(db, university_id)

    if not config:
        raise ValueError(
            "Payment configuration not found"
        )

    if provider is not None:
        config.provider = provider

    if currency is not None:
        config.currency = currency.upper()

    if merchant_name is not None:
        config.merchant_name = merchant_name

    if configuration_data is not None:
        config.configuration_data = json.dumps(
            configuration_data
        )

    if is_enabled is not None:
        config.is_enabled = is_enabled

    db.commit()
    db.refresh(config)

    return config


# ============================================================
# UNIVERSITY FEES
# ============================================================

def create_university_fee(
    db: Session,
    university_id: int,
    name: str,
    code: str,
    amount: float,
    fee_type: str = "general",
    currency: str | None = None,
    description: str | None = None,
    clearance_stage_id: int | None = None,
    is_required: bool = True,
):
    if amount <= 0:
        raise ValueError(
            "Fee amount must be greater than zero"
        )

    existing = (
        db.query(UniversityFee)
        .filter(
            UniversityFee.university_id == university_id,
            UniversityFee.code == code,
        )
        .first()
    )

    if existing:
        raise ValueError(
            f"Fee '{code}' already exists"
        )

    config = get_payment_config(
        db,
        university_id,
    )

    final_currency = (
        currency.upper()
        if currency
        else (
            config.currency
            if config
            else "NGN"
        )
    )

    fee = UniversityFee(
        university_id=university_id,
        name=name,
        code=code,
        amount=amount,
        currency=final_currency,
        fee_type=fee_type,
        description=description,
        clearance_stage_id=clearance_stage_id,
        is_required=is_required,
        status="active",
    )

    db.add(fee)
    db.commit()
    db.refresh(fee)

    return fee


def list_university_fees(
    db: Session,
    university_id: int,
    active_only: bool = True,
):
    query = (
        db.query(UniversityFee)
        .filter(
            UniversityFee.university_id == university_id
        )
    )

    if active_only:
        query = query.filter(
            UniversityFee.status == "active"
        )

    return query.order_by(
        UniversityFee.id.asc()
    ).all()


def deactivate_university_fee(
    db: Session,
    university_id: int,
    fee_id: int,
):
    fee = (
        db.query(UniversityFee)
        .filter(
            UniversityFee.id == fee_id,
            UniversityFee.university_id == university_id,
        )
        .first()
    )

    if not fee:
        raise ValueError("University fee not found")

    fee.status = "inactive"

    db.commit()
    db.refresh(fee)

    return fee


# ============================================================
# INVOICES
# ============================================================

def _generate_invoice_number():
    return (
        "ALOKO-"
        + datetime.now(timezone.utc).strftime("%Y%m%d")
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )


def create_payment_invoice(
    db: Session,
    university_id: int,
    student_id: int,
    fee_id: int,
    clearance_id: int | None = None,
    due_date=None,
):
    fee = (
        db.query(UniversityFee)
        .filter(
            UniversityFee.id == fee_id,
            UniversityFee.university_id == university_id,
            UniversityFee.status == "active",
        )
        .first()
    )

    if not fee:
        raise ValueError(
            "Active university fee not found"
        )

    invoice = PaymentInvoice(
        university_id=university_id,
        student_id=student_id,
        fee_id=fee.id,
        clearance_id=clearance_id,
        invoice_number=_generate_invoice_number(),
        amount=fee.amount,
        currency=fee.currency,
        status="pending",
        due_date=due_date,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoice(
    db: Session,
    university_id: int,
    invoice_id: int,
):
    return (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.id == invoice_id,
            PaymentInvoice.university_id == university_id,
        )
        .first()
    )


def get_student_invoices(
    db: Session,
    university_id: int,
    student_id: int,
):
    return (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.university_id == university_id,
            PaymentInvoice.student_id == student_id,
        )
        .order_by(
            PaymentInvoice.created_at.desc()
        )
        .all()
    )


# ============================================================
# TRANSACTIONS
# ============================================================

def create_payment_transaction(
    db: Session,
    university_id: int,
    invoice_id: int,
    provider: str | None = None,
    transaction_reference: str | None = None,
):
    invoice = get_invoice(
        db,
        university_id,
        invoice_id,
    )

    if not invoice:
        raise ValueError("Invoice not found")

    if invoice.status != "pending":
        raise ValueError(
            "Invoice is no longer payable"
        )

    transaction = PaymentTransaction(
        university_id=university_id,
        student_id=invoice.student_id,
        invoice_id=invoice.id,
        provider=provider,
        transaction_reference=(
            transaction_reference
            or uuid.uuid4().hex
        ),
        amount=invoice.amount,
        currency=invoice.currency,
        status="pending",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def get_transaction(
    db: Session,
    university_id: int,
    transaction_id: int,
):
    return (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.id == transaction_id,
            PaymentTransaction.university_id == university_id,
        )
        .first()
    )


def update_transaction_status(
    db: Session,
    university_id: int,
    transaction_id: int,
    status: str,
    provider_response: dict | None = None,
):
    if status not in VALID_TRANSACTION_STATUSES:
        raise ValueError(
            f"Invalid transaction status: {status}"
        )

    transaction = get_transaction(
        db,
        university_id,
        transaction_id,
    )

    if not transaction:
        raise ValueError(
            "Payment transaction not found"
        )

    transaction.status = status

    if provider_response is not None:
        transaction.provider_response = json.dumps(
            provider_response
        )

    if status == "successful":
        transaction.paid_at = _now()

        invoice = get_invoice(
            db,
            university_id,
            transaction.invoice_id,
        )

        if invoice:
            invoice.status = "paid"

    db.commit()
    db.refresh(transaction)

    return transaction


# ============================================================
# PAYMENT VERIFICATION
# ============================================================

def create_payment_verification(
    db: Session,
    university_id: int,
    transaction_id: int,
    verification_method: str = "manual",
):
    transaction = get_transaction(
        db,
        university_id,
        transaction_id,
    )

    if not transaction:
        raise ValueError(
            "Payment transaction not found"
        )

    existing = (
        db.query(PaymentVerification)
        .filter(
            PaymentVerification.transaction_id
            == transaction_id,
            PaymentVerification.university_id
            == university_id,
            PaymentVerification.status
            == "pending",
        )
        .first()
    )

    if existing:
        raise ValueError(
            "Pending verification already exists"
        )

    verification = PaymentVerification(
        university_id=university_id,
        transaction_id=transaction_id,
        verification_method=verification_method,
        status="pending",
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    return verification


def verify_payment(
    db: Session,
    university_id: int,
    verification_id: int,
    verified_by: int,
    verification_reference: str | None = None,
    notes: str | None = None,
):
    verification = (
        db.query(PaymentVerification)
        .filter(
            PaymentVerification.id == verification_id,
            PaymentVerification.university_id == university_id,
        )
        .first()
    )

    if not verification:
        raise ValueError(
            "Payment verification not found"
        )

    if verification.status != "pending":
        raise ValueError(
            "Verification has already been processed"
        )

    transaction = get_transaction(
        db,
        university_id,
        verification.transaction_id,
    )

    if not transaction:
        raise ValueError(
            "Payment transaction not found"
        )

    verification.status = "verified"
    verification.verified_by = verified_by
    verification.verification_reference = (
        verification_reference
    )
    verification.notes = notes
    verification.verified_at = _now()

    transaction.status = "successful"
    transaction.paid_at = _now()

    invoice = get_invoice(
        db,
        university_id,
        transaction.invoice_id,
    )

    if invoice:
        invoice.status = "paid"

    db.commit()
    db.refresh(verification)

    return verification


def reject_payment(
    db: Session,
    university_id: int,
    verification_id: int,
    verified_by: int,
    notes: str,
):
    if not notes or not notes.strip():
        raise ValueError(
            "Rejection reason is required"
        )

    verification = (
        db.query(PaymentVerification)
        .filter(
            PaymentVerification.id == verification_id,
            PaymentVerification.university_id == university_id,
        )
        .first()
    )

    if not verification:
        raise ValueError(
            "Payment verification not found"
        )

    if verification.status != "pending":
        raise ValueError(
            "Verification has already been processed"
        )

    verification.status = "rejected"
    verification.verified_by = verified_by
    verification.notes = notes.strip()
    verification.verified_at = _now()

    transaction = get_transaction(
        db,
        university_id,
        verification.transaction_id,
    )

    if transaction:
        transaction.status = "failed"

    db.commit()
    db.refresh(verification)

    return verification


# ============================================================
# WEBHOOKS
# ============================================================

def record_payment_webhook(
    db: Session,
    university_id: int,
    provider: str,
    payload: dict,
    event_type: str | None = None,
    transaction_reference: str | None = None,
):
    webhook = PaymentWebhook(
        university_id=university_id,
        provider=provider,
        event_type=event_type,
        transaction_reference=transaction_reference,
        payload=json.dumps(payload),
        processing_status="received",
    )

    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return webhook


def mark_webhook_processed(
    db: Session,
    webhook_id: int,
    university_id: int,
):
    webhook = (
        db.query(PaymentWebhook)
        .filter(
            PaymentWebhook.id == webhook_id,
            PaymentWebhook.university_id == university_id,
        )
        .first()
    )

    if not webhook:
        raise ValueError("Payment webhook not found")

    webhook.processing_status = "processed"
    webhook.processed_at = _now()

    db.commit()
    db.refresh(webhook)

    return webhook


# ============================================================
# CLEARANCE PAYMENT INTEGRATION
# ============================================================

def mark_clearance_payment_verified(
    db: Session,
    university_id: int,
    transaction_id: int,
):
    from app.university_ai.models.clearance import (
        StudentClearance,
    )

    transaction = get_transaction(
        db,
        university_id,
        transaction_id,
    )

    if not transaction:
        raise ValueError(
            "Payment transaction not found"
        )

    if transaction.status != "successful":
        raise ValueError(
            "Payment has not been successfully completed"
        )

    invoice = get_invoice(
        db,
        university_id,
        transaction.invoice_id,
    )

    if not invoice:
        raise ValueError("Invoice not found")

    if not invoice.clearance_id:
        raise ValueError(
            "Invoice is not linked to a clearance"
        )

    clearance = (
        db.query(StudentClearance)
        .filter(
            StudentClearance.id
            == invoice.clearance_id,
            StudentClearance.university_id
            == university_id,
        )
        .first()
    )

    if not clearance:
        raise ValueError(
            "Clearance not found"
        )

    clearance.payment_status = "verified"

    db.commit()
    db.refresh(clearance)

    return clearance


# ============================================================
# DASHBOARD / SUMMARY
# ============================================================

def get_payment_summary(
    db: Session,
    university_id: int,
    student_id: int | None = None,
):
    invoice_query = db.query(PaymentInvoice).filter(
        PaymentInvoice.university_id == university_id
    )

    transaction_query = db.query(
        PaymentTransaction
    ).filter(
        PaymentTransaction.university_id == university_id
    )

    if student_id is not None:
        invoice_query = invoice_query.filter(
            PaymentInvoice.student_id == student_id
        )

        transaction_query = transaction_query.filter(
            PaymentTransaction.student_id == student_id
        )

    invoices = invoice_query.all()
    transactions = transaction_query.all()

    total_invoiced = sum(
        invoice.amount
        for invoice in invoices
    )

    total_paid = sum(
        transaction.amount
        for transaction in transactions
        if transaction.status == "successful"
    )

    pending = sum(
        1
        for invoice in invoices
        if invoice.status == "pending"
    )

    return {
        "invoice_count": len(invoices),
        "transaction_count": len(transactions),
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "pending_invoices": pending,
        "currency": (
            invoices[0].currency
            if invoices
            else "NGN"
        ),
    }