from datetime import datetime, timedelta
from bson import ObjectId
from app.core.config import settings
from app.models.complaint import ComplaintStatus, ComplaintCategory, Priority


async def generate_ticket_id(db):
    today = datetime.utcnow().strftime("%Y%m%d")
    count = await db.complaints.count_documents({
        "created_at": {
            "$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        }
    })
    return f"CMP-{today}-{str(count + 1).zfill(4)}"


async def create_complaint(db, user_id: str, complaint_data: dict) -> dict:
    ticket_id = await generate_ticket_id(db)

    complaint_doc = {
        "title": complaint_data["title"],
        "description": complaint_data["description"],
        "category": complaint_data["category"],
        "location": {
            "type": "Point",
            "coordinates": [complaint_data["longitude"], complaint_data["latitude"]],
        },
        "address": complaint_data.get("address"),
        "images": complaint_data.get("images", []),
        "status": ComplaintStatus.PENDING,
        "priority": complaint_data.get("priority", Priority.MEDIUM),
        "submitted_by": user_id,
        "assigned_to": None,
        "escalated": False,
        "escalation_level": 0,
        "resolution_notes": None,
        "resolution_images": [],
        "ticket_id": ticket_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Create 2dsphere index for geospatial queries
    await db.complaints.create_index([("location", "2dsphere")])

    result = await db.complaints.insert_one(complaint_doc)
    complaint_doc["_id"] = result.inserted_id
    return complaint_doc


async def get_complaint_by_id(db, complaint_id: str) -> dict:
    try:
        complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
        return complaint
    except Exception:
        return None


async def get_complaints_by_user(db, user_id: str, page: int = 1, limit: int = 20, status_filter=None):
    query = {"submitted_by": user_id}
    if status_filter:
        query["status"] = status_filter

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).skip(skip).limit(limit).sort("created_at", -1)
    complaints = await cursor.to_list(length=limit)
    return {
        "complaints": complaints,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def get_all_complaints(
    db, page: int = 1, limit: int = 20,
    status_filter=None, category_filter=None, escalated_only=False
):
    query = {}
    if status_filter:
        query["status"] = status_filter
    if category_filter:
        query["category"] = category_filter
    if escalated_only:
        query["escalated"] = True

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).skip(skip).limit(limit).sort("created_at", -1)
    complaints = await cursor.to_list(length=limit)
    return {
        "complaints": complaints,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def get_officer_complaints(db, officer_id: str, page: int = 1, limit: int = 20):
    query = {"assigned_to": officer_id}
    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).skip(skip).limit(limit).sort("created_at", -1)
    complaints = await cursor.to_list(length=limit)
    return {
        "complaints": complaints,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def update_complaint_status(db, complaint_id: str, status: ComplaintStatus, resolution_notes=None):
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow(),
    }
    if status == ComplaintStatus.RESOLVED:
        update_data["resolved_at"] = datetime.utcnow()
    if resolution_notes:
        update_data["resolution_notes"] = resolution_notes

    result = await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": update_data},
    )
    return result.modified_count > 0


async def assign_complaint(db, complaint_id: str, officer_id: str):
    update_data = {
        "assigned_to": officer_id,
        "status": ComplaintStatus.IN_PROGRESS,
        "updated_at": datetime.utcnow(),
    }
    result = await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": update_data},
    )
    return result.modified_count > 0


async def escalate_complaints(db):
    """Find all pending complaints older than escalation_days and escalate them."""
    threshold = datetime.utcnow() - timedelta(days=settings.escalation_days)
    pending_complaints = await db.complaints.find({
        "status": ComplaintStatus.PENDING,
        "escalated": False,
        "created_at": {"$lt": threshold},
    }).to_list(length=1000)

    escalated_ids = []
    for complaint in pending_complaints:
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
        escalated_ids.append(complaint["_id"])

    return escalated_ids


async def get_nearby_complaints(db, longitude: float, latitude: float, radius_km: float = 5):
    complaints = await db.complaints.find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "$maxDistance": radius_km * 1000,
            }
        }
    }).to_list(length=50)
    return complaints


async def get_dashboard_stats(db):
    total = await db.complaints.count_documents({})
    pending = await db.complaints.count_documents({"status": ComplaintStatus.PENDING})
    in_progress = await db.complaints.count_documents({"status": ComplaintStatus.IN_PROGRESS})
    resolved = await db.complaints.count_documents({"status": ComplaintStatus.RESOLVED})
    escalated = await db.complaints.count_documents({"escalated": True})
    resolution_rate = (resolved / total * 100) if total > 0 else 0

    # Average resolution time
    pipeline = [
        {"$match": {"status": ComplaintStatus.RESOLVED, "resolved_at": {"$ne": None}}},
        {"$project": {
            "resolution_time": {"$subtract": ["$resolved_at", "$created_at"]}
        }},
        {"$group": {"_id": None, "avg_time": {"$avg": "$resolution_time"}}}
    ]
    result = await db.complaints.aggregate(pipeline).to_list(length=1)
    avg_hours = None
    if result and result[0].get("avg_time"):
        avg_hours = result[0]["avg_time"] / (1000 * 3600)

    return {
        "total_complaints": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "escalated": escalated,
        "resolution_rate": round(resolution_rate, 1),
        "avg_resolution_time_hours": round(avg_hours, 1) if avg_hours else None,
    }


async def get_category_stats(db):
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    result = await db.complaints.aggregate(pipeline).to_list(length=20)
    return [{"category": r["_id"], "count": r["count"]} for r in result]


async def add_complaint_images(db, complaint_id: str, image_urls: list):
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"images": {"$each": image_urls}}},
    )


async def add_resolution_images(db, complaint_id: str, image_urls: list):
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": {"resolution_images": image_urls, "updated_at": datetime.utcnow()}},
    )
