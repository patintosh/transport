import smtplib
from email.message import EmailMessage
import os

def send_email_alert(subject, body):
    smtp_host = os.getenv("AIR_CORSICA_SMTP_HOST")
    smtp_port = int(os.getenv("AIR_CORSICA_SMTP_PORT", "587"))
    smtp_user = os.getenv("AIR_CORSICA_SMTP_USER")
    smtp_pass = os.getenv("AIR_CORSICA_SMTP_PASS")
    to_email = os.getenv("AIR_CORSICA_ALERT_EMAIL")

    if not all([smtp_host, smtp_user, smtp_pass, to_email]):
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
