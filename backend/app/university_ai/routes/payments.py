from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User

from app.university_ai.models.payment import (
    PaymentInvoice,
    PaymentTransaction,
    PaymentVerification,
)

from app.university_ai.services.university_admin_auth import (
    require_university_admin,
    require_university_access,
)
from app.university_ai.services.student_auth import require_student

from app.university_ai.services.payment import (
    create_payment_config,
    get_payment_config,
    update_payment_config,
    create_university_fee,
    list_university_fees,
    deactivate_university_fee,
    create_payment_invoice,
    get_invoice,
    get_student_invoices,
    create_payment_transaction,
    get_transaction,
    update_transaction_status,
    create_payment_verification,
    verify_payment,
    reject_payment,
    record_payment_webhook,
    mark_webhook_processed,
    mark_clearance_payment_verified,
    get_payment_summary,
)


router = APIRouter(
    prefix="/university/payments",
    tags=["University Payments"],
)


# ============================================================
# PAYLOADS
# ============================================================

class PaymentConfigCreate(BaseModel):
    university_id: int
    provider: str | None = None
    merchant_id: str | None = None
    secret_key: str | None = None
    public_key: str | None = None
    currency: str = "NGN"
    enabled: bool = False


class PaymentConfigUpdate(BaseModel):
    provider: str | None = None
    merchant_id: str | None = None
    secret_key: str | None = None
    public_key: str | None = None
    currency: str | None = None
    enabled: bool | None = None


class FeeCreate(BaseModel):
    university_id: int
    name: str
    code: str
    description: str | None = None
    amount: float
    currency: str | None = None
    academic_session_id: int | None = None
    clearance_stage_id: int | None = None
    mandatory: bool = True


class InvoiceCreate(BaseModel):
    university_id: int
    student_id: int
    fee_id: int
    clearance_id: int | None = None
    amount: float | None = None
    currency: str | None = None
    description: str | None = None


class TransactionCreate(BaseModel):
    university_id: int
    student_id: int | None = None
    invoice_id: int
    provider: str | None = None
    transaction_reference: str | None = None
    amount: float | None = None
    currency: str | None = None


class TransactionStatusUpdate(BaseModel):
    status: str


class VerificationCreate(BaseModel):
    transaction_id: int
    verification_reference: str | None = None
    notes: str | None = None


class WebhookCreate(BaseModel):
    university_id: int
    provider: str
    event_type: str | None = None
    event_reference: str | None = None
    payload: dict


class ClearancePaymentVerify(BaseModel):
    clearance_id: int
    invoice_id: int


# ============================================================
# PAYMENT CONFIG
# ============================================================

@router.post("/config")
def create_config(
    payload: PaymentConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    configuration_data = {
        "merchant_id": payload.merchant_id,
        "secret_key": payload.secret_key,
        "public_key": payload.public_key,
    }

    return create_payment_config(
        db=db,
        university_id=payload.university_id,
        provider=payload.provider,
        currency=payload.currency,
        merchant_name=payload.merchant_id,
        configuration_data=configuration_data,
        is_enabled=payload.enabled,
    )


@router.get("/config/{university_id}")
def get_config(
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return get_payment_config(
        db=db,
        university_id=university_id,
    )


@router.put("/config/{university_id}")
def update_config(
    university_id: int,
    payload: PaymentConfigUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    configuration_data = None

    if (
        payload.merchant_id is not None
        or payload.secret_key is not None
        or payload.public_key is not None
    ):
        configuration_data = {
            "merchant_id": payload.merchant_id,
            "secret_key": payload.secret_key,
            "public_key": payload.public_key,
        }

    return update_payment_config(
        db=db,
        university_id=university_id,
        provider=payload.provider,
        currency=payload.currency,
        merchant_name=payload.merchant_id,
        configuration_data=configuration_data,
        is_enabled=payload.enabled,
    )


# ============================================================
# FEES
# ============================================================

@router.post("/fees")
def create_fee(
    payload: FeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    return create_university_fee(
        db=db,
        university_id=payload.university_id,
        name=payload.name,
        code=payload.code,
        amount=payload.amount,
        fee_type="general",
        currency=payload.currency,
        description=payload.description,
        clearance_stage_id=payload.clearance_stage_id,
        is_required=payload.mandatory,
    )


@router.get("/fees/{university_id}")
def list_fees(
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return list_university_fees(
        db=db,
        university_id=university_id,
    )


@router.delete("/fees/{university_id}/{fee_id}")
def deactivate_fee(
    university_id: int,
    fee_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return deactivate_university_fee(
        db=db,
        university_id=university_id,
        fee_id=fee_id,
    )


# ============================================================
# INVOICES
# ============================================================

@router.post("/invoices")
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    return create_payment_invoice(
        db=db,
        university_id=payload.university_id,
        student_id=payload.student_id,
        fee_id=payload.fee_id,
        clearance_id=payload.clearance_id,
    )


@router.get("/invoices/{university_id}/{invoice_id}")
def get_invoice_route(
    university_id: int,
    invoice_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    result = get_invoice(
        db=db,
        university_id=university_id,
        invoice_id=invoice_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    return result


@router.get("/student/invoices")
def get_my_invoices(
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    return get_student_invoices(
        db=db,
        university_id=student.university_id,
        student_id=student.id,
    )


# ============================================================
# TRANSACTIONS
# ============================================================

@router.post("/transactions")
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=payload.university_id,
        db=db,
        current_user=current_user,
    )

    invoice = get_invoice(
        db=db,
        university_id=payload.university_id,
        invoice_id=payload.invoice_id,
    )

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    if (
        payload.student_id is not None
        and payload.student_id != invoice.student_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Student does not match invoice.",
        )

    return create_payment_transaction(
        db=db,
        university_id=payload.university_id,
        invoice_id=payload.invoice_id,
        provider=payload.provider,
        transaction_reference=payload.transaction_reference,
    )


@router.get("/transactions/{university_id}/{transaction_id}")
def get_transaction_route(
    university_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    result = get_transaction(
        db=db,
        university_id=university_id,
        transaction_id=transaction_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Payment transaction not found",
        )

    return result


@router.get("/student/transactions")
def get_my_transactions(
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    invoices = get_student_invoices(
        db=db,
        university_id=student.university_id,
        student_id=student.id,
    )

    invoice_ids = {invoice.id for invoice in invoices}

    if not invoice_ids:
        return []

    return (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.university_id == student.university_id,
            PaymentTransaction.student_id == student.id,
            PaymentTransaction.invoice_id.in_(invoice_ids),
        )
        .order_by(PaymentTransaction.id.desc())
        .all()
    )


@router.patch("/transactions/{transaction_id}/status")
def update_transaction_status_route(
    transaction_id: int,
    payload: TransactionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    transaction = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.id == transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Payment transaction not found",
        )

    require_university_access(
        university_id=transaction.university_id,
        db=db,
        current_user=current_user,
    )

    return update_transaction_status(
        db=db,
        university_id=transaction.university_id,
        transaction_id=transaction_id,
        status=payload.status,
    )


# ============================================================
# PAYMENT VERIFICATION
# ============================================================

@router.post("/verifications")
def create_verification(
    payload: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    transaction = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.id == payload.transaction_id)
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Payment transaction not found",
        )

    require_university_access(
        university_id=transaction.university_id,
        db=db,
        current_user=current_user,
    )

    return create_payment_verification(
        db=db,
        university_id=transaction.university_id,
        transaction_id=payload.transaction_id,
    )


@router.post("/verifications/{verification_id}/verify")
def verify_payment_route(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    verification = (
        db.query(PaymentVerification)
        .filter(PaymentVerification.id == verification_id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Payment verification not found",
        )

    require_university_access(
        university_id=verification.university_id,
        db=db,
        current_user=current_user,
    )

    return verify_payment(
        db=db,
        university_id=verification.university_id,
        verification_id=verification_id,
        verified_by=current_user.id,
    )


@router.post("/verifications/{verification_id}/reject")
def reject_payment_route(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    verification = (
        db.query(PaymentVerification)
        .filter(PaymentVerification.id == verification_id)
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Payment verification not found",
        )

    require_university_access(
        university_id=verification.university_id,
        db=db,
        current_user=current_user,
    )

    return reject_payment(
        db=db,
        university_id=verification.university_id,
        verification_id=verification_id,
        verified_by=current_user.id,
        notes="Payment verification rejected.",
    )


# ============================================================
# PAYMENT WEBHOOK
# ============================================================

@router.post("/webhooks")
def payment_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
):
    """
    Machine-to-machine endpoint.

    This endpoint intentionally does not use normal JWT authentication.
    The payment provider must be authenticated at the provider/webhook
    layer before this endpoint is used in production.
    """

    return record_payment_webhook(
        db=db,
        university_id=payload.university_id,
        provider=payload.provider,
        event_type=payload.event_type,
        transaction_reference=payload.event_reference,
        payload=payload.payload,
    )


@router.post("/webhooks/{webhook_id}/processed")
def process_webhook(
    webhook_id: int,
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    require_university_access(
        university_id=university_id,
        db=db,
        current_user=current_user,
    )

    try:
        return mark_webhook_processed(
            db=db,
            webhook_id=webhook_id,
            university_id=university_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


# ============================================================
# CLEARANCE PAYMENT
# ============================================================

@router.post("/clearance/verify-payment")
def verify_clearance_payment(
    payload: ClearancePaymentVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_university_admin),
):
    invoice = (
        db.query(PaymentInvoice)
        .filter(PaymentInvoice.id == payload.invoice_id)
        .first()
    )

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    require_university_access(
        university_id=invoice.university_id,
        db=db,
        current_user=current_user,
    )

    if invoice.clearance_id != payload.clearance_id:
        raise HTTPException(
            status_code=400,
            detail="Invoice does not belong to the specified clearance.",
        )

    transaction = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.university_id == invoice.university_id,
            PaymentTransaction.invoice_id == invoice.id,
            PaymentTransaction.status == "successful",
        )
        .order_by(PaymentTransaction.id.desc())
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=400,
            detail="No successful payment transaction found for this invoice.",
        )

    return mark_clearance_payment_verified(
        db=db,
        university_id=invoice.university_id,
        transaction_id=transaction.id,
    )


# ============================================================
# SUMMARY
# ============================================================

@router.get("/summary/{university_id}")
def payment_summary(
    university_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_university_access),
):
    return get_payment_summary(
        db=db,
        university_id=university_id,
    )
