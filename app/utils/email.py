import smtplib
from email.message import EmailMessage
import os

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your OTP Code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"""
Your OTP code is: {otp}

This code will expire in 5 minutes.
If you did not request this, please ignore this email.
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
