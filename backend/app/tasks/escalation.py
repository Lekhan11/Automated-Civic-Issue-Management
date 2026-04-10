import asyncio
from app.tasks.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def check_escalations_async():
    """Run multi-level escalation check."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    try:
        from app.services.complaint_service import escalate_complaints
        result = await escalate_complaints(db)
        print(f"[ESCALATION] Level 1: {result['level1_escalated']}, Level 2: {result['level2_escalated']}")
        return result
    finally:
        client.close()


@celery_app.task(name="app.tasks.escalation.check_escalations")
def check_escalations():
    """Celery task: runs hourly to check and escalate complaints."""
    return asyncio.run(check_escalations_async())
