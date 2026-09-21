
import asyncio
import json
import os
import urllib.request
from email.message import EmailMessage

import aiosmtplib
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# EMAIL CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", "").strip()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM = os.getenv("RESEND_FROM", "").strip()

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    os.getenv("PUBLIC_BASE_URL", ""),
).strip()


# ============================================================
# RESEND
# ============================================================

def _send_resend_email_sync(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    if not RESEND_FROM:
        raise RuntimeError("RESEND_FROM is not configured.")

    payload = {
        "from": RESEND_FROM,
        "to": [recipient],
        "subject": subject,
        "text": text_body,
    }

    if html_body:
        payload["html"] = html_body

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        response_body = response.read().decode("utf-8")

    if response.status < 200 or response.status >= 300:
        raise RuntimeError(
            f"Resend email request failed: HTTP {response.status} "
            f"{response_body}"
        )


async def _send_resend_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    await asyncio.to_thread(
        _send_resend_email_sync,
        recipient,
        subject,
        text_body,
        html_body,
    )


# ============================================================
# SMTP FALLBACK
# ============================================================

def _validate_smtp_config():
    missing = []

    if not SMTP_HOST:
        missing.append("SMTP_HOST")

    if not SMTP_USERNAME:
        missing.append("SMTP_USERNAME")

    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")

    if not SMTP_FROM:
        missing.append("SMTP_FROM")

    if missing:
        raise RuntimeError(
            "Email service is not configured. Missing: "
            + ", ".join(missing)
        )


async def _send_smtp_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    _validate_smtp_config()

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(text_body)

    if html_body:
        message.add_alternative(
            html_body,
            subtype="html",
        )

    use_tls = SMTP_PORT == 465

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        use_tls=use_tls,
        start_tls=False if use_tls else True,
        timeout=20,
    )


# ============================================================
# UNIFIED EMAIL SENDER
# ============================================================

async def _send_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    # Production: Resend HTTPS API.
    if RESEND_API_KEY:
        await _send_resend_email(
            recipient=recipient,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        return

    # Local development fallback: Gmail SMTP.
    await _send_smtp_email(
        recipient=recipient,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


# ============================================================
# VERIFICATION EMAIL
# ============================================================

async def send_verification_email(
    recipient: str,
    code: str,
    expires_minutes: int,
):
    subject = "Verify your Aloko account"

    text_body = f"""Hello,

Your Aloko email verification code is:

{code}

This code expires in {expires_minutes} minutes.

If you did not create an Aloko account, you can ignore this email.

— Aloko
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<body>
    <h2>Verify your Aloko account</h2>

    <p>Your email verification code is:</p>

    <p style="font-size: 28px; font-weight: bold; letter-spacing: 6px;">
        {code}
    </p>

    <p>This code expires in {expires_minutes} minutes.</p>

    <p>
        If you did not create an Aloko account,
        you can ignore this email.
    </p>

    <p>— Aloko</p>
</body>
</html>
"""

    await _send_email(
        recipient=recipient,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


# ============================================================
# PASSWORD RESET EMAIL
# ============================================================

async def send_password_reset_email(
    recipient: str,
    token: str,
    expires_minutes: int,
):
    if not FRONTEND_URL:
        raise RuntimeError(
            "FRONTEND_URL or PUBLIC_BASE_URL must be configured."
        )

    reset_url = (
        FRONTEND_URL.rstrip("/")
        + "/?reset_token="
        + token
    )

    subject = "Reset your Aloko password"

    text_body = f"""Hello,

A password reset was requested for your Aloko account.

Use this link to create a new password:

{reset_url}

This link expires in {expires_minutes} minutes and can only be used once.

If you did not request a password reset, you can ignore this email.

— Aloko
"""

    html_body = f"""
<!DOCTYPE html>
<html>
<body>
    <h2>Reset your Aloko password</h2>

    <p>
        A password reset was requested for your Aloko account.
    </p>

    <p>
        <a href="{reset_url}">
            Reset your password
        </a>
    </p>

    <p>
        This link expires in {expires_minutes} minutes
        and can only be used once.
    </p>

    <p>
        If you did not request a password reset,
        you can ignore this email.
    </p>

    <p>— Aloko</p>
</body>
</html>
"""

    await _send_email(
        recipient=recipient,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )