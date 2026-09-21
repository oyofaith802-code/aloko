import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.university_ai.models.people import Student
from app.university_ai.models.student_invitation import StudentInvitation
from app.models.user import User
from app.core.security import create_access_token
from app.services.email_service import (
    send_verification_email,
    send_password_reset_email,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==========================================================
# REQUEST MODELS
# ==========================================================

class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ResendVerificationRequest(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ==========================================================
# HELPERS
# ==========================================================

VERIFICATION_CODE_EXPIRE_MINUTES = 10
PASSWORD_RESET_EXPIRE_MINUTES = 30


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def set_verification_code(user: User) -> str:
    code = generate_verification_code()

    user.verification_code_hash = (
        hash_verification_code(code)
    )

    user.verification_code_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=VERIFICATION_CODE_EXPIRE_MINUTES
        )
    )

    return code


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(48)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def set_password_reset_token(user: User) -> str:
    token = generate_password_reset_token()

    user.password_reset_token_hash = (
        hash_password_reset_token(token)
    )

    user.password_reset_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=PASSWORD_RESET_EXPIRE_MINUTES
        )
    )

    return token


# ==========================================================
# SIGNUP
# ==========================================================

@router.post("/signup")
def signup(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    email = normalize_email(user.email)

    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered.",
        )

    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    new_user = User(
        email=email,
        password_hash=password_hash,
        email_verified=False,
        auth_provider="email",
    )

    db.add(new_user)
    db.flush()

    # ------------------------------------------------------
    # LINK PENDING UNIVERSITY STUDENT INVITATIONS
    # ------------------------------------------------------
    from datetime import datetime, timezone

    pending_invitations = (
        db.query(StudentInvitation)
        .filter(
            StudentInvitation.email == email,
            StudentInvitation.status == "pending",
            StudentInvitation.expires_at > datetime.now(timezone.utc),
        )
        .all()
    )

    linked_invitations = 0

    for invitation in pending_invitations:
        if not invitation.student_id:
            continue

        student = (
            db.query(Student)
            .filter(
                Student.id == invitation.student_id,
                Student.university_id == invitation.university_id,
                Student.status == "active",
            )
            .first()
        )

        if not student:
            continue

        if student.user_id is not None:
            continue

        student.user_id = new_user.id

        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)

        linked_invitations += 1

    # ------------------------------------------------------
    # EMAIL VERIFICATION
    # ------------------------------------------------------
    code = set_verification_code(new_user)

    db.commit()
    db.refresh(new_user)

    asyncio.run(
        send_verification_email(
            recipient=new_user.email,
            code=code,
            expires_minutes=VERIFICATION_CODE_EXPIRE_MINUTES,
        )
    )

    return {
        "message": "Account created. Please verify your email.",
        "verification_required": True,
        "user_id": new_user.id,
        "email": new_user.email,
        "student_invitation_linked": linked_invitations > 0,
        "linked_invitations": linked_invitations,
    }


# ==========================================================
# VERIFY EMAIL
# ==========================================================

@router.post("/verify-email")
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(
        data.email
    )

    code = data.code.strip()

    if not code.isdigit() or len(code) != 6:
        raise HTTPException(
            status_code=400,
            detail="Verification code must be 6 digits.",
        )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    if user.email_verified:
        token = create_access_token(
            user.id,
            user.email,
        )

        return {
            "message": "Email is already verified.",
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
        }

    if not user.verification_code_hash:
        raise HTTPException(
            status_code=400,
            detail="No verification code is active. Request a new code.",
        )

    expires_at = (
        user.verification_code_expires_at
    )

    if not expires_at:
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired.",
        )

    now = datetime.now(timezone.utc)

    if expires_at < now:
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired. Request a new code.",
        )

    submitted_hash = (
        hash_verification_code(code)
    )

    if submitted_hash != user.verification_code_hash:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code.",
        )

    user.email_verified = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None

    db.commit()
    db.refresh(user)

    token = create_access_token(
        user.id,
        user.email,
    )

    return {
        "message": "Email verified successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
    }


# ==========================================================
# RESEND VERIFICATION CODE
# ==========================================================

@router.post("/resend-verification")
def resend_verification(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(
        data.email
    )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    if user.email_verified:
        return {
            "message": "Email is already verified.",
            "verified": True,
        }

    code = set_verification_code(
        user
    )

    db.commit()

    asyncio.run(
        send_verification_email(
            recipient=user.email,
            code=code,
            expires_minutes=VERIFICATION_CODE_EXPIRE_MINUTES,
        )
    )

    return {
        "message": "A new verification code has been generated.",
        "verification_required": True,
    }


# ==========================================================
# FORGOT PASSWORD
# ==========================================================

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(data.email)

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Always return the same response so the endpoint does not
    # reveal whether an email address is registered.
    if not user:
        return {
            "message": "If an account exists for this email, a password reset link will be sent."
        }

    # Google-only accounts do not have a local password.
    if (
        user.auth_provider == "google"
        and not user.password_hash
    ):
        return {
            "message": "If an account exists for this email, a password reset link will be sent."
        }

    token = set_password_reset_token(user)
    db.commit()

    asyncio.run(
        send_password_reset_email(
            recipient=user.email,
            token=token,
            expires_minutes=PASSWORD_RESET_EXPIRE_MINUTES,
        )
    )

    return {
        "message": "If an account exists for this email, a password reset link will be sent."
    }


# ==========================================================
# RESET PASSWORD
# ==========================================================

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    token = data.token.strip()

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Reset token is required.",
        )

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    token_hash = hash_password_reset_token(token)

    user = (
        db.query(User)
        .filter(
            User.password_reset_token_hash == token_hash,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset token.",
        )

    expires_at = user.password_reset_expires_at

    if not expires_at:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset token.",
        )

    now = datetime.now(timezone.utc)

    if expires_at < now:
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset token.",
        )

    user.password_hash = bcrypt.hashpw(
        data.new_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    # Single-use token: invalidate immediately.
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None

    db.commit()

    return {
        "message": "Password reset successfully. You can now sign in."
    }


# ==========================================================
# LOGIN
# ==========================================================

@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    email = normalize_email(
        user.email
    )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # ------------------------------------------------------
    # GOOGLE ACCOUNT
    # ------------------------------------------------------

    if (
        existing_user.auth_provider == "google"
        and not existing_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "This account uses Google Sign-In. "
                "Please continue with Google."
            ),
        )

    if not existing_user.password_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    password_valid = bcrypt.checkpw(
        user.password.encode("utf-8"),
        existing_user.password_hash.encode("utf-8"),
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # ------------------------------------------------------
    # EMAIL VERIFICATION
    # ------------------------------------------------------

    if not existing_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail=(
                "Email not verified. "
                "Please verify your email before signing in."
            ),
        )

    token = create_access_token(
        existing_user.id,
        existing_user.email,
    )

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user_id": existing_user.id,
        "email": existing_user.email,
    }