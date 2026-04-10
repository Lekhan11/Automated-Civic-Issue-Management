import asyncio
from bson import ObjectId
from app.tasks.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.notification_service import (
    send_email,
    build_assignment_email,
    build_escalation_email,
    build_resolution_email,
)


def _get_db():
    client = AsyncIOMotorClient(settings.mongodb_url)
    return client[settings.database_name], client


@celery_app.task(
    name="app.tasks.notification.send_assignment_notification",
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=3,
)
def send_assignment_notification(officer_id: str, complaint_id: str, ticket_id: str):
    async def _send():
        db, client = _get_db()
        try:
            user = await db.users.find_one({"_id": ObjectId(officer_id)})
            complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
            if user and complaint:
                body = build_assignment_email(
                    complaint["title"], ticket_id,
                    str(complaint.get("ward_number", "N/A"))
                )
                await send_email(user["email"], f"New Complaint Assigned: {ticket_id}", body)
        finally:
            client.close()
    asyncio.run(_send())


@celery_app.task(
    name="app.tasks.notification.send_escalation_notification",
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=3,
)
def send_escalation_notification(officer_id: str, complaint_id: str, ticket_id: str, level: int):
    async def _send():
        db, client = _get_db()
        try:
            user = await db.users.find_one({"_id": ObjectId(officer_id)})
            complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
            if user and complaint:
                body = build_escalation_email(ticket_id, level, complaint["title"])
                await send_email(user["email"], f"Complaint Escalated (Level {level}): {ticket_id}", body)
        finally:
            client.close()
    asyncio.run(_send())


@celery_app.task(
    name="app.tasks.notification.send_resolution_notification",
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=3,
)
def send_resolution_notification(user_id: str, complaint_id: str, ticket_id: str, resolution_notes: str):
    async def _send():
        db, client = _get_db()
        try:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
            if user and complaint:
                body = build_resolution_email(ticket_id, complaint["title"], resolution_notes)
                await send_email(user["email"], f"Complaint Resolved: {ticket_id}", body)
        finally:
            client.close()
    asyncio.run(_send())
