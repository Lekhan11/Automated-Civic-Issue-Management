import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.config import settings
from app.models.complaint import ComplaintStatus, ComplaintCategory, Priority
from app.models.user import UserRole


async def generate_ticket_id(db):
    today = datetime.utcnow().strftime("%Y%m%d")
    count = await db.complaints.count_documents({
        "created_at": {
            "$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        }
    })
    return f"CMP-{today}-{str(count + 1).zfill(4)}"


# ---- Area Resolution ----

async def resolve_area_from_coordinates(db, latitude: float, longitude: float) -> dict:
    """Reverse geocode coordinates to area. Returns dict with area_id, area_name, ward_number, zone, district, geocoded_area_name."""
    from geopy.geocoders import Nominatim
    from app.services.area_service import get_area_by_name

    geolocator = Nominatim(user_agent=settings.nominatim_user_agent)
    geocoded_area_name = None
    geocoded_zone = None

    try:
        location = await asyncio.to_thread(
            geolocator.reverse, f"{latitude}, {longitude}"
        )
        if location and location.raw:
            address_data = location.raw.get("address", {})
            geocoded_area_name = (
                address_data.get("village")
                or address_data.get("suburb")
                or address_data.get("neighbourhood")
                or address_data.get("city_district")
                or address_data.get("town")
                or address_data.get("city")
            )
            geocoded_zone = (
                address_data.get("county")
                or address_data.get("state_district")
            )
    except Exception:
        geocoded_area_name = None

    result = {"area_id": None, "area_name": None, "ward_number": None, "zone": None, "district": None, "geocoded_area_name": geocoded_area_name}

    if geocoded_area_name:
        area = await get_area_by_name(db, geocoded_area_name)

        # Fallback: case-insensitive partial match
        if not area:
            area = await db.areas.find_one({
                "name": {"$regex": geocoded_area_name, "$options": "i"},
                "is_active": True,
            })

        # Fallback: match within the geocoded zone context
        if not area and geocoded_zone:
            area = await db.areas.find_one({
                "name": {"$regex": geocoded_area_name, "$options": "i"},
                "zone": {"$regex": geocoded_zone, "$options": "i"},
                "is_active": True,
            })

        if area:
            result["area_id"] = str(area["_id"])
            result["area_name"] = area["name"]
            result["ward_number"] = area["ward_number"]
            result["zone"] = area["zone"]
            result["district"] = area["district"]

    return result


async def find_officer_for_area(db, area_id: str, role: UserRole):
    """Find an active officer of given role assigned to a specific area."""
    return await db.users.find_one({
        "role": role,
        "assigned_area_id": area_id,
        "is_active": True,
    })


# ---- Complaint CRUD ----

async def create_complaint(db, user_id: str, complaint_data: dict) -> dict:
    ticket_id = await generate_ticket_id(db)
    latitude = complaint_data["latitude"]
    longitude = complaint_data["longitude"]

    # Resolve area from coordinates
    area_info = await resolve_area_from_coordinates(db, latitude, longitude)

    complaint_doc = {
        "title": complaint_data["title"],
        "description": complaint_data["description"],
        "category": complaint_data["category"],
        "location": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "address": complaint_data.get("address"),
        "images": complaint_data.get("images", []),
        "status": ComplaintStatus.PENDING,
        "priority": complaint_data.get("priority", Priority.MEDIUM),
        "submitted_by": user_id,
        "assigned_to": None,
        "escalated": False,
        "escalated_to": None,
        "escalation_level": 0,
        "resolution_notes": None,
        "resolution_images": [],
        "ticket_id": ticket_id,
        "area_id": area_info.get("area_id"),
        "ward_number": area_info.get("ward_number"),
        "zone": area_info.get("zone"),
        "district": area_info.get("district"),
        "area_name": area_info.get("area_name"),
        "geocoded_area_name": area_info.get("geocoded_area_name"),
        "assigned_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await db.complaints.create_index([("location", "2dsphere")])
    await db.complaints.create_index([("area_id", 1)])

    result = await db.complaints.insert_one(complaint_doc)
    complaint_doc["_id"] = result.inserted_id

    # Auto-assign local officer if area matched
    if area_info.get("area_id"):
        officer = await find_officer_for_area(db, area_info["area_id"], UserRole.LOCAL_OFFICER)
        if officer:
            now = datetime.utcnow()
            await db.complaints.update_one(
                {"_id": result.inserted_id},
                {"$set": {
                    "assigned_to": str(officer["_id"]),
                    "status": ComplaintStatus.IN_PROGRESS,
                    "assigned_at": now,
                    "updated_at": now,
                }},
            )
            complaint_doc["assigned_to"] = str(officer["_id"])
            complaint_doc["status"] = ComplaintStatus.IN_PROGRESS
            complaint_doc["assigned_at"] = now

            # Trigger async notification
            try:
                from app.tasks.notification import send_assignment_notification
                send_assignment_notification.delay(
                    str(officer["_id"]), str(result.inserted_id), ticket_id
                )
            except Exception:
                pass  # Celery broker may not be running

    return complaint_doc


async def get_complaint_by_id(db, complaint_id: str) -> dict:
    try:
        return await db.complaints.find_one({"_id": ObjectId(complaint_id)})
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


# ---- Officer Complaints (Area-Scoped) ----

async def get_officer_complaints(db, officer_id: str, page: int = 1, limit: int = 20, status_filter=None):
    """For local_officers: complaints from their assigned area.
    For zonal_officers: complaints from their assigned zone.
    For district_officers: all complaints.
    Fallback: only directly assigned complaints."""
    officer = await db.users.find_one({"_id": ObjectId(officer_id)})
    if not officer:
        return {"complaints": [], "total": 0, "page": page, "pages": 0}

    query = {}
    role = officer.get("role")

    if role == UserRole.LOCAL_OFFICER.value and officer.get("assigned_area_id"):
        query["area_id"] = officer["assigned_area_id"]
    elif role == UserRole.ZONAL_OFFICER.value and officer.get("assigned_zone"):
        query["zone"] = officer["assigned_zone"]
    elif role == UserRole.DISTRICT_OFFICER.value:
        pass  # See all complaints in district
    else:
        # Fallback: show only directly assigned
        query["assigned_to"] = officer_id

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

    if result.modified_count > 0 and status == ComplaintStatus.RESOLVED:
        complaint = await get_complaint_by_id(db, complaint_id)
        if complaint and complaint.get("submitted_by"):
            try:
                from app.tasks.notification import send_resolution_notification
                send_resolution_notification.delay(
                    str(complaint["submitted_by"]), complaint_id,
                    complaint["ticket_id"], resolution_notes or ""
                )
            except Exception:
                pass

    return result.modified_count > 0


async def assign_complaint(db, complaint_id: str, officer_id: str):
    now = datetime.utcnow()
    update_data = {
        "assigned_to": officer_id,
        "status": ComplaintStatus.IN_PROGRESS,
        "assigned_at": now,
        "updated_at": now,
    }
    result = await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": update_data},
    )

    if result.modified_count > 0:
        complaint = await get_complaint_by_id(db, complaint_id)
        if complaint:
            try:
                from app.tasks.notification import send_assignment_notification
                send_assignment_notification.delay(
                    officer_id, complaint_id, complaint["ticket_id"]
                )
            except Exception:
                pass

    return result.modified_count > 0


# ---- Multi-Level Escalation ----

async def _escalate_to_district_officer(db, complaint: dict, now: datetime):
    """Escalate a complaint directly to a district officer."""
    district_officer = await db.users.find_one({
        "role": UserRole.DISTRICT_OFFICER, "is_active": True,
    })

    district_id = str(district_officer["_id"]) if district_officer else None

    update = {
        "escalated": True,
        "status": ComplaintStatus.ESCALATED,
        "escalation_level": 2,
        "escalated_to": district_id,
        "assigned_to": district_id,
        "assigned_at": now,
        "escalated_at": now,
        "updated_at": now,
    }

    if district_id:
        await db.complaints.update_one({"_id": complaint["_id"]}, {"$set": update})
        try:
            from app.tasks.notification import send_escalation_notification
            send_escalation_notification.delay(
                district_id, str(complaint["_id"]), complaint["ticket_id"], 2
            )
        except Exception:
            pass


async def escalate_complaints(db) -> dict:
    """Multi-level escalation:
    - Level 0 -> Level 1 (Local -> Zonal): after escalation_level1_days from assigned_at
    - Level 1 -> Level 2 (Zonal -> District Officer): after escalation_level2_days from assigned_at
    Returns: {"level1_escalated": int, "level2_escalated": int}
    """
    now = datetime.utcnow()
    stats = {"level1_escalated": 0, "level2_escalated": 0}

    # --- Level 0 -> Level 1: Escalate to Zonal Officer ---
    level1_threshold = now - timedelta(days=settings.escalation_level1_days)

    complaints_for_level1 = await db.complaints.find({
        "status": {"$in": [ComplaintStatus.IN_PROGRESS, ComplaintStatus.PENDING]},
        "escalation_level": 0,
        "assigned_at": {"$lt": level1_threshold, "$ne": None},
        "escalated": False,
    }).to_list(length=500)

    for complaint in complaints_for_level1:
        zone = complaint.get("zone")
        if not zone:
            await _escalate_to_district_officer(db, complaint, now)
            stats["level2_escalated"] += 1
            continue

        zonal_officer = await db.users.find_one({
            "role": UserRole.ZONAL_OFFICER,
            "assigned_zone": zone,
            "is_active": True,
        })

        if zonal_officer:
            await db.complaints.update_one(
                {"_id": complaint["_id"]},
                {"$set": {
                    "escalated": True,
                    "status": ComplaintStatus.ESCALATED,
                    "escalation_level": 1,
                    "escalated_to": str(zonal_officer["_id"]),
                    "assigned_to": str(zonal_officer["_id"]),
                    "assigned_at": now,
                    "escalated_at": now,
                    "updated_at": now,
                }},
            )
            try:
                from app.tasks.notification import send_escalation_notification
                send_escalation_notification.delay(
                    str(zonal_officer["_id"]), str(complaint["_id"]),
                    complaint["ticket_id"], 1
                )
            except Exception:
                pass
            stats["level1_escalated"] += 1

    # --- Level 1 -> Level 2: Escalate to District Officer ---
    level2_threshold = now - timedelta(days=settings.escalation_level2_days)

    complaints_for_level2 = await db.complaints.find({
        "status": ComplaintStatus.ESCALATED,
        "escalation_level": 1,
        "assigned_at": {"$lt": level2_threshold},
    }).to_list(length=500)

    for complaint in complaints_for_level2:
        await _escalate_to_district_officer(db, complaint, now)
        stats["level2_escalated"] += 1

    # --- Unassigned complaints older than level1 threshold ---
    unassigned_old = await db.complaints.find({
        "status": ComplaintStatus.PENDING,
        "assigned_to": None,
        "created_at": {"$lt": level1_threshold},
    }).to_list(length=200)

    for complaint in unassigned_old:
        await _escalate_to_district_officer(db, complaint, now)
        stats["level2_escalated"] += 1

    return stats


# ---- Geospatial & Stats ----

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
