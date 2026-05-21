import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _send_email(to_email: str, subject: str, body: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)
    if not smtp_host or not smtp_user:
        return
    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(smtp_host, smtp_port) as srv:
        srv.starttls()
        srv.login(smtp_user, smtp_pass)
        srv.send_message(msg)


def send_reset_email(to_email: str, token: str, frontend_url: str, reset_minutes: int = 30) -> None:
    reset_link = f"{frontend_url}/reset-password?token={token}"
    body = (
        f"You requested a password reset.\n\n"
        f"Click the link below (valid for {reset_minutes} minutes):\n{reset_link}\n\n"
        f"If you did not request this, you can ignore this email."
    )
    _send_email(to_email, "OrbitPay — Password Reset Request", body)


def send_welcome_email(to_email: str, full_name: str, temp_password: str, frontend_url: str) -> None:
    login_url = f"{frontend_url}/login"
    body = (
        f"Hello {full_name},\n\n"
        f"Your OrbitPay employee account has been created.\n\n"
        f"Login details:\n"
        f"  URL:      {login_url}\n"
        f"  Email:    {to_email}\n"
        f"  Password: {temp_password}\n\n"
        f"You will be prompted to change your password on first login.\n\n"
        f"Please keep these credentials secure and change your password after logging in.\n\n"
        f"— The OrbitPay Team"
    )
    _send_email(to_email, "OrbitPay — Your Account Has Been Created", body)
