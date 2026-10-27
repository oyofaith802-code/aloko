import os
import secrets
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.billing.models import AlokoSubscription


router = APIRouter(prefix="/billing", tags=["Aloko Subscription Billing"])

PRICES = {
    "NGN": {"amount": 2000000, "display": "₦20,000"},
}
PRODUCT = "customer_support"


class CheckoutRequest(BaseModel):
    currency: str = Field(default="NGN", pattern="^NGN$")


def paystack_headers():
    key = os.getenv("PAYSTACK_SECRET_KEY", "").strip()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="Paystack billing is not configured on the server.",
        )
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def user_email(user: User) -> str:
    email = getattr(user, "email", None)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Your account needs a valid email address for checkout.",
        )
    return email


@router.post("/customer-support/checkout")
def create_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    currency = data.currency
    price = PRICES[currency]

    # Do not create duplicate concurrent checkout attempts for an active plan.
    now = datetime.now(timezone.utc)
    active = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == PRODUCT,
            AlokoSubscription.status == "active",
            AlokoSubscription.period_end > now,
        )
        .first()
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail="You already have an active Customer Support AI subscription.",
        )

    reference = "ALOKO-" + secrets.token_hex(16)
    row = AlokoSubscription(
        user_id=user.id,
        product=PRODUCT,
        provider="paystack",
        reference=reference,
        currency=currency,
        amount_minor=price["amount"],
        status="pending",
    )
    db.add(row)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if not frontend_url.startswith("https://"):
        # Do not send customers to an insecure or unspecified callback.
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Set FRONTEND_URL to your HTTPS frontend URL in the server environment.",
        )

    payload = {
        "email": user_email(user),
        "amount": price["amount"],
        "currency": currency,
        "reference": reference,
        "callback_url": f"{frontend_url}/billing/callback",
        "channels": ["card", "bank_transfer"],
        "metadata": {
            "user_id": str(user.id),
            "product": PRODUCT,
        },
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=paystack_headers(),
            json=payload,
            timeout=20,
        )
        result = response.json()
    except HTTPException:
        raise
    except Exception:
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Could not initialize checkout.")

    if response.status_code >= 400 or not result.get("status"):
        # Log the provider's reason for diagnosis; never log request headers or secrets.
        provider_message = str(result.get("message") or "No provider message")[:500]
        print(
            f"Paystack checkout rejected: HTTP {response.status_code}; "
            f"message={provider_message}; currency={currency}"
        )
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Payment provider rejected checkout.")

    return {
        "success": True,
        "reference": reference,
        "currency": currency,
        "amount_minor": price["amount"],
        "display_price": price["display"],
        "authorization_url": result["data"]["authorization_url"],
    }


@router.post("/customer-support/verify/{reference}")
def verify_checkout(
    reference: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.reference == reference,
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == PRODUCT,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Payment reference not found.")

    # Never let a failed or already processed attempt activate access.
    if row.status == "active" and row.period_end:
        return {
            "success": True,
            "status": "active",
            "period_end": row.period_end,
        }

    if row.status not in ("pending", "verification_failed"):
        raise HTTPException(
            status_code=409,
            detail="This payment attempt cannot be verified again.",
        )

    try:
        response = requests.get(
            "https://api.paystack.co/transaction/verify/"
            + requests.utils.quote(reference, safe=""),
            headers=paystack_headers(),
            timeout=20,
        )
        result = response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Payment verification is unavailable.")

    payment = result.get("data") or {}
    if (
        response.status_code >= 400
        or not result.get("status")
        or payment.get("status") != "success"
        or payment.get("reference") != row.reference
        or payment.get("currency") != row.currency
        or payment.get("amount") != row.amount_minor
    ):
        # Keep unconfirmed payments pending so the customer can retry verification.
        raise HTTPException(
            status_code=402,
            detail="Payment is not confirmed. No subscription access has been granted.",
        )

    paid_at = datetime.now(timezone.utc)
    if payment.get("paid_at"):
        try:
            paid_at = datetime.fromisoformat(
                payment["paid_at"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    row.status = "active"
    row.paid_at = paid_at
    row.period_end = paid_at + timedelta(days=30)
    db.commit()
    db.refresh(row)

    return {
        "success": True,
        "status": row.status,
        "product": row.product,
        "currency": row.currency,
        "period_end": row.period_end,
    }


@router.get("/customer-support/status")
def subscription_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    row = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == PRODUCT,
            AlokoSubscription.status == "active",
            AlokoSubscription.period_end > now,
        )
        .order_by(AlokoSubscription.period_end.desc())
        .first()
    )
    if not row:
        return {"success": True, "active": False}

    return {
        "success": True,
        "active": True,
        "product": row.product,
        "currency": row.currency,
        "period_end": row.period_end,
    }


BUSINESS_PRODUCT = "business_ai"
BUSINESS_AMOUNT = 2000000


@router.post("/business-ai/checkout")
def create_business_ai_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    active = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == BUSINESS_PRODUCT,
            AlokoSubscription.status == "active",
            AlokoSubscription.period_end > now,
        )
        .first()
    )
    if active:
        raise HTTPException(status_code=409, detail="Your Business AI subscription is already active.")

    reference = "ALOKO-" + secrets.token_hex(16)
    row = AlokoSubscription(
        user_id=user.id,
        product=BUSINESS_PRODUCT,
        provider="paystack",
        reference=reference,
        currency="NGN",
        amount_minor=BUSINESS_AMOUNT,
        status="pending",
    )
    db.add(row)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if not frontend_url.startswith("https://"):
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(status_code=503, detail="Set FRONTEND_URL to your HTTPS frontend URL.")

    payload = {
        "email": user_email(user),
        "amount": BUSINESS_AMOUNT,
        "currency": "NGN",
        "reference": reference,
        "callback_url": f"{frontend_url}/billing/callback?product=business_ai",
        "channels": ["card", "bank_transfer"],
        "metadata": {"user_id": str(user.id), "product": BUSINESS_PRODUCT},
    }
    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=paystack_headers(),
            json=payload,
            timeout=20,
        )
        result = response.json()
    except Exception:
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Could not initialize Business AI checkout.")

    if response.status_code >= 400 or not result.get("status"):
        row.status = "initialization_failed"
        db.commit()
        raise HTTPException(status_code=502, detail="Paystack rejected Business AI checkout.")

    return {
        "success": True,
        "reference": reference,
        "currency": "NGN",
        "amount_minor": BUSINESS_AMOUNT,
        "display_price": "₦20,000",
        "authorization_url": result["data"]["authorization_url"],
    }


@router.post("/business-ai/verify/{reference}")
def verify_business_ai_checkout(
    reference: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.reference == reference,
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == BUSINESS_PRODUCT,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Business AI payment reference not found.")

    if row.status == "active" and row.period_end and row.period_end > datetime.now(timezone.utc):
        return {"success": True, "status": "active", "period_end": row.period_end}

    if row.status not in ("pending", "verification_failed"):
        raise HTTPException(status_code=409, detail="This payment attempt cannot be verified again.")

    try:
        response = requests.get(
            "https://api.paystack.co/transaction/verify/" + requests.utils.quote(reference, safe=""),
            headers=paystack_headers(),
            timeout=20,
        )
        result = response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Payment verification is unavailable.")

    payment = result.get("data") or {}
    if (
        response.status_code >= 400
        or not result.get("status")
        or payment.get("status") != "success"
        or payment.get("reference") != row.reference
        or payment.get("currency") != "NGN"
        or payment.get("amount") != BUSINESS_AMOUNT
    ):
        raise HTTPException(status_code=402, detail="Payment is not confirmed. Business AI access has not been granted.")

    paid_at = datetime.now(timezone.utc)
    if payment.get("paid_at"):
        try:
            paid_at = datetime.fromisoformat(payment["paid_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    row.status = "active"
    row.paid_at = paid_at
    row.period_end = paid_at + timedelta(days=30)
    db.commit()
    db.refresh(row)
    return {"success": True, "status": "active", "product": BUSINESS_PRODUCT, "period_end": row.period_end}


@router.get("/business-ai/status")
def business_ai_subscription_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    row = (
        db.query(AlokoSubscription)
        .filter(
            AlokoSubscription.user_id == user.id,
            AlokoSubscription.product == BUSINESS_PRODUCT,
            AlokoSubscription.status == "active",
            AlokoSubscription.period_end > now,
        )
        .order_by(AlokoSubscription.period_end.desc())
        .first()
    )
    if not row:
        return {"success": True, "active": False}
    return {"success": True, "active": True, "product": BUSINESS_PRODUCT, "period_end": row.period_end}

