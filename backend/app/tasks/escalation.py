from datetime import datetime
from app.tasks.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.complaint import ComplaintStatus
import asyncio


async def escalate_complaints_async():
    """Find and escalate complaints that have been pending for too long."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    try:
        threshold = datetime.utcnow() - __import__("datetime").timedelta(days=settings.escalation_days)

        # Find pending complaints older than threshold
        pending_complaints = await db.complaints.find({
            "status": ComplaintStatus.PENDING,
            "escalated": False,
            "created_at": {"$lt": threshold},
        }).to_list(length=1000)

        escalated_count = 0
        for complaint in pending_complaints:
            # Update complaint status
            await db.complaints.update_one(
                {"_id": complaint["_id"]},
                {"$set": {
                    "escalated": True,
                    "status": ComplaintStatus.ESCALATED,
                    "escalated_at": datetime.utcnow(),
                    "escalation_level": complaint.get("escalation_level", 0) + 1,
                    "updated_at": datetime.utcnow(),
                }},
            )

            # Get submitter info for notification
            submitter = await db.users.find_one({"_id": complaint["submitted_by"]})

            # Get super admins to notify
            super_admins = await db.users.find({"role": "super_admin"}).to_list(length=10)

            # Send notification (you can implement email sending here)
            # await send_escalation_email(complaint, submitter, super_admins)

            escalated_count += 1
            print(f"Escalated complaint {complaint['ticket_id']}")

        return escalated_count
    finally:
        client.close()


@celery_app.task(name="app.tasks.escalation.check_escalations")
def check_escalations():
    """Celery task to check and escalate complaints."""
    return asyncio.run(escalate_complaints_async())


@celery_app.task(name="app.tasks.escalation.send_notification")
def send_notification(user_id: str, message: str):
    """Send notification to user (can be email, push, etc.)"""
    print(f"Notification sent to {user_id}: {message}")
    return True