import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an SMTP email. Returns True on success."""
    if not settings.smtp_user or not settings.smtp_password:
        print(f"[EMAIL] Not configured. Would send to {to_email}: {subject}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html"))

    try:
        await asyncio.to_thread(_send_smtp, msg)
        print(f"[EMAIL] Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send to {to_email}: {e}")
        return False


def _send_smtp(msg: MIMEMultipart):
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def build_assignment_email(complaint_title: str, ticket_id: str, ward: str) -> str:
    return f"""
    <h2>New Complaint Assigned</h2>
    <p>A new complaint has been assigned to you:</p>
    <ul>
        <li><strong>Ticket:</strong> {ticket_id}</li>
        <li><strong>Title:</strong> {complaint_title}</li>
        <li><strong>Ward:</strong> {ward}</li>
    </ul>
    <p>Please log in to the system to take action.</p>
    """


def build_escalation_email(ticket_id: str, escalation_level: int, complaint_title: str) -> str:
    level_names = {1: "Zonal Officer", 2: "District Officer"}
    return f"""
    <h2>Complaint Escalated - Level {escalation_level}</h2>
    <p>A complaint has been escalated to you at Level {escalation_level} ({level_names.get(escalation_level, 'Unknown')}):</p>
    <ul>
        <li><strong>Ticket:</strong> {ticket_id}</li>
        <li><strong>Title:</strong> {complaint_title}</li>
    </ul>
    <p>Please review and take appropriate action.</p>
    """


def build_resolution_email(ticket_id: str, complaint_title: str, resolution_notes: str) -> str:
    return f"""
    <h2>Complaint Resolved</h2>
    <p>Your complaint has been resolved:</p>
    <ul>
        <li><strong>Ticket:</strong> {ticket_id}</li>
        <li><strong>Title:</strong> {complaint_title}</li>
        <li><strong>Resolution:</strong> {resolution_notes or 'No notes provided'}</li>
    </ul>
    <p>Thank you for using CivicFix.</p>
    """
