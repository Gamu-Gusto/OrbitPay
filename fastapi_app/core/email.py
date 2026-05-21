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


def send_registration_received_email(to_email: str, full_name: str) -> None:
    body = (
        f"Hello {full_name},\n\n"
        f"Thank you for registering with OrbitPay.\n\n"
        f"Your registration request has been received and is currently under review.\n"
        f"You will be notified by email once your account has been reviewed.\n\n"
        f"— The OrbitPay Team"
    )
    _send_email(to_email, "OrbitPay — Registration Request Received", body)


def send_registration_approved_email(to_email: str, full_name: str, frontend_url: str) -> None:
    login_url = f"{frontend_url}/login?tab=staff"
    body = (
        f"Hello {full_name},\n\n"
        f"Great news — your OrbitPay account has been approved!\n\n"
        f"You can now log in using the credentials you registered with:\n"
        f"  URL:   {login_url}\n"
        f"  Email: {to_email}\n\n"
        f"Use the 'Staff Access' tab to sign in.\n\n"
        f"— The OrbitPay Team"
    )
    _send_email(to_email, "OrbitPay — Your Account Has Been Approved", body)


def send_registration_rejected_email(to_email: str, full_name: str, reason: str) -> None:
    body = (
        f"Hello {full_name},\n\n"
        f"We have reviewed your OrbitPay registration request and unfortunately "
        f"we are unable to approve it at this time.\n\n"
        f"Reason: {reason or 'Not specified'}\n\n"
        f"If you believe this is an error or have questions, please contact us.\n\n"
        f"— The OrbitPay Team"
    )
    _send_email(to_email, "OrbitPay — Registration Not Approved", body)


def send_activation_email(to_email: str, full_name: str, role: str, activation_link: str) -> None:
    body = (
        f"Hello {full_name},\n\n"
        f"You have been invited to OrbitPay as {role}.\n\n"
        f"Click the link below to activate your account and set your password:\n"
        f"{activation_link}\n\n"
        f"This link expires in 72 hours.\n\n"
        f"If you did not expect this email, you can safely ignore it.\n\n"
        f"— The OrbitPay Team"
    )
    _send_email(to_email, "You have been invited to OrbitPay", body)


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
