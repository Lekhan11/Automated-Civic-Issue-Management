import asyncio
import logging
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.complaint import ComplaintStatus, ComplaintCategory, Priority
from app.models.user import UserRole

logger = logging.getLogger(__name__)


# ---- Helpers ----

def _sql_complaint_to_dict(c) -> dict:
    from sqlalchemy.inspection import inspect
    if c is None:
        return None
    data = {}
    mapper = inspect(c).mapper
    for column in mapper.columns:
        value = getattr(c, column.key)
        if column.key in ("status", "category", "priority"):
            data[column.key] = value.value if value else None
        elif column.key == "location" and value is not None:
            from geoalchemy2.shape import to_shape
            shape = to_shape(value)
            data["location"] = {"type": "Point", "coordinates": [shape.x, shape.y]}
        else:
            data[column.key] = value
    data["_id"] = str(data["id"])
    return data


async def generate_ticket_id(db):
    today = datetime.utcnow().strftime("%Y%m%d")
    if settings.use_supabase:
        from app.models.sql_models import SQLComplaint
        from sqlalchemy import select, func, cast, Date
        count_q = select(func.count()).select_from(SQLComplaint).where(
            cast(SQLComplaint.created_at, Date) == datetime.utcnow().date()
        )
        result = await db.execute(count_q)
        count = result.scalar() or 0
    else:
        count = await db.complaints.count_documents({
            "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
        })
    return f"CMP-{today}-{str(count + 1).zfill(4)}"


# ---- Area Resolution ----

async def resolve_area_from_coordinates(db, latitude: float, longitude: float) -> dict:
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent=settings.nominatim_user_agent)
    geocoded_area_name = None
    geocoded_zone = None
    geocoded_village = None
    geocoded_town = None

    try:
        location = await asyncio.to_thread(
            geolocator.reverse, f"{latitude}, {longitude}"
        )
        if location and location.raw:
            address_data = location.raw.get("address", {})
            logger.debug(f"Nominatim reverse geocoding result for ({latitude}, {longitude}): {address_data}")
            geocoded_village = address_data.get("village") or address_data.get("hamlet")
            geocoded_town = address_data.get("town") or address_data.get("city")
            geocoded_area_name = (
                geocoded_village
                or address_data.get("suburb")
                or address_data.get("neighbourhood")
                or address_data.get("city_district")
                or geocoded_town
            )
            geocoded_zone = (
                address_data.get("county")
                or address_data.get("state_district")
            )
    except Exception as e:
        logger.error(f"Error during Nominatim reverse geocoding for ({latitude}, {longitude}): {str(e)}")
        geocoded_area_name = None

    result = {"area_id": None, "area_name": None, "ward_number": None, "zone": None, "district": None, "geocoded_area_name": geocoded_area_name}

    from app.services.area_service import get_nearby_areas, get_area_by_name, find_areas_by_name_regex

    # Primary method: find nearest areas by geospatial distance (get top 5 candidates)
    candidate_areas = []
    try:
        candidate_areas = await get_nearby_areas(db, latitude, longitude, limit=5)
        if not candidate_areas:
            logger.warning(f"No areas with coordinates found near ({latitude}, {longitude})")
    except Exception as e:
        logger.warning(f"Geospatial query failed: {e}")

    # If we have candidates, score them based on text match with geocoded name
    best_area = None
    if candidate_areas and geocoded_area_name:
        scored_candidates = []
        for area in candidate_areas:
            score = 0
            area_name = area["name"].lower()
            geocoded_lower = geocoded_area_name.lower()

            if area_name == geocoded_lower:
                score += 100
            elif geocoded_lower in area_name or area_name in geocoded_lower:
                score += 50
            else:
                for suffix in ("veedu", "palayam", "patti", "puram", "natham"):
                    if area_name.endswith(suffix):
                        area_stem = area_name[:-len(suffix)]
                        if area_stem and (area_stem in geocoded_lower or geocoded_lower in area_stem):
                            score += 30
                            break

            scored_candidates.append((score, area))

        if scored_candidates:
            best_score, best_candidate = max(scored_candidates, key=lambda x: x[0])
            if best_score > 0:
                best_area = best_candidate
                logger.debug(f"Selected area {best_candidate['name']} (score: {best_score}) from {len(candidate_areas)} candidates")

    if not best_area and candidate_areas:
        best_area = candidate_areas[0]
        logger.debug(f"Using nearest area {best_area['name']} (no text match)")

    if best_area:
        logger.info(f"Resolved area: {best_area['name']} in zone {best_area['zone']}, district {best_area['district']}")
        result["area_id"] = str(best_area["_id"])
        result["area_name"] = best_area["name"]
        result["ward_number"] = best_area["ward_number"]
        result["zone"] = best_area["zone"]
        result["district"] = best_area["district"]
    else:
        # Fallback: pure text matching
        logger.debug(f"Geospatial method failed, falling back to text matching for ({latitude}, {longitude})")
        if geocoded_area_name:
            area = await get_area_by_name(db, geocoded_area_name)
            if not area:
                matches = await find_areas_by_name_regex(db, geocoded_area_name)
                area = matches[0] if matches else None
            if not area and geocoded_zone:
                matches = await find_areas_by_name_regex(db, geocoded_area_name, geocoded_zone)
                area = matches[0] if matches else None

            if area:
                logger.info(f"Text fallback matched area: {area['name']} (zone: {area['zone']}, district: {area['district']})")
                result["area_id"] = str(area["_id"])
                result["area_name"] = area["name"]
                result["ward_number"] = area["ward_number"]
                result["zone"] = area["zone"]
                result["district"] = area["district"]

    return result


async def find_officer_for_area(db, area_id: str, role: UserRole):
    from app.services.user_service import get_officers_by_area
    officers = await get_officers_by_area(db, area_id, role.value if isinstance(role, UserRole) else role)
    return officers[0] if officers else None


# ---- Complaint CRUD ----

async def create_complaint(db, user_id: str, complaint_data: dict) -> dict:
    if settings.use_supabase:
        return await _create_complaint_sql(db, user_id, complaint_data)
    return await _create_complaint_mongo(db, user_id, complaint_data)


async def _create_complaint_sql(db, user_id: str, complaint_data: dict) -> dict:
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import text
    import uuid

    ticket_id = await generate_ticket_id(db)
    latitude = complaint_data["latitude"]
    longitude = complaint_data["longitude"]

    area_info = await resolve_area_from_coordinates(db, latitude, longitude)

    complaint = SQLComplaint(
        id=uuid.uuid4(),
        ticket_id=ticket_id,
        title=complaint_data["title"],
        description=complaint_data["description"],
        category=complaint_data["category"],
        status=ComplaintStatus.PENDING,
        priority=complaint_data.get("priority", Priority.MEDIUM),
        latitude=latitude,
        longitude=longitude,
        address=complaint_data.get("address"),
        images=complaint_data.get("images", []),
        submitted_by=uuid.UUID(user_id),
        assigned_to=None,
        escalated=False,
        escalated_to=None,
        escalation_level=0,
        resolution_notes=None,
        resolution_images=[],
        area_id=uuid.UUID(area_info["area_id"]) if area_info.get("area_id") else None,
        ward_number=area_info.get("ward_number"),
        zone=area_info.get("zone"),
        district=area_info.get("district"),
        area_name=area_info.get("area_name"),
        geocoded_area_name=area_info.get("geocoded_area_name"),
        assigned_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Set PostGIS point
    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    complaint.location = text(f"ST_GeomFromText('{point_wkt}')").label("location")

    db.add(complaint)
    await db.flush()

    # Auto-assign local officer
    assigned_to_id = None
    if area_info.get("area_id"):
        officer = await find_officer_for_area(db, area_info["area_id"], UserRole.LOCAL_OFFICER)
        if officer:
            assigned_to_id = officer["_id"]
            now = datetime.utcnow()
            complaint.assigned_to = uuid.UUID(assigned_to_id)
            complaint.status = ComplaintStatus.IN_PROGRESS
            complaint.assigned_at = now
            complaint.updated_at = now

            try:
                from app.tasks.notification import send_assignment_notification
                send_assignment_notification.delay(assigned_to_id, str(complaint.id), ticket_id)
            except Exception:
                pass

    await db.commit()
    await db.refresh(complaint)
    return _sql_complaint_to_dict(complaint)


async def _create_complaint_mongo(db, user_id: str, complaint_data: dict) -> dict:
    from bson import ObjectId

    ticket_id = await generate_ticket_id(db)
    latitude = complaint_data["latitude"]
    longitude = complaint_data["longitude"]

    area_info = await resolve_area_from_coordinates(db, latitude, longitude)

    complaint_doc = {
        "title": complaint_data["title"],
        "description": complaint_data["description"],
        "category": complaint_data["category"],
        "location": {"type": "Point", "coordinates": [longitude, latitude]},
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

            try:
                from app.tasks.notification import send_assignment_notification
                send_assignment_notification.delay(
                    str(officer["_id"]), str(result.inserted_id), ticket_id
                )
            except Exception:
                pass

    return complaint_doc


async def get_complaint_by_id(db, complaint_id: str):
    if settings.use_supabase:
        return await _get_complaint_by_id_sql(db, complaint_id)
    return await _get_complaint_by_id_mongo(db, complaint_id)


async def _get_complaint_by_id_sql(db, complaint_id: str):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select
    import uuid

    try:
        result = await db.execute(select(SQLComplaint).where(SQLComplaint.id == uuid.UUID(complaint_id)))
        c = result.scalar_one_or_none()
        return _sql_complaint_to_dict(c) if c else None
    except (ValueError, Exception):
        return None


async def _get_complaint_by_id_mongo(db, complaint_id: str):
    from bson import ObjectId
    try:
        return await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    except Exception:
        return None


async def get_complaints_by_user(db, user_id: str, page: int = 1, limit: int = 20, status_filter=None):
    if settings.use_supabase:
        return await _get_complaints_by_user_sql(db, user_id, page, limit, status_filter)
    return await _get_complaints_by_user_mongo(db, user_id, page, limit, status_filter)


async def _get_complaints_by_user_sql(db, user_id: str, page: int = 1, limit: int = 20, status_filter=None):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, func
    import uuid

    conditions = [SQLComplaint.submitted_by == uuid.UUID(user_id)]
    if status_filter:
        conditions.append(SQLComplaint.status == status_filter)

    total = (await db.execute(select(func.count()).select_from(SQLComplaint).where(*conditions))).scalar()

    result = await db.execute(
        select(SQLComplaint)
        .where(*conditions)
        .order_by(SQLComplaint.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    complaints = [_sql_complaint_to_dict(c) for c in result.scalars().all()]
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


async def _get_complaints_by_user_mongo(db, user_id: str, page: int = 1, limit: int = 20, status_filter=None):
    query = {"submitted_by": user_id}
    if status_filter:
        query["status"] = status_filter

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).skip(skip).limit(limit).sort("created_at", -1)
    complaints = await cursor.to_list(length=limit)
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


async def get_all_complaints(db, page: int = 1, limit: int = 20, status_filter=None, category_filter=None, escalated_only=False):
    if settings.use_supabase:
        return await _get_all_complaints_sql(db, page, limit, status_filter, category_filter, escalated_only)
    return await _get_all_complaints_mongo(db, page, limit, status_filter, category_filter, escalated_only)


async def _get_all_complaints_sql(db, page=1, limit=20, status_filter=None, category_filter=None, escalated_only=False):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, func

    conditions = []
    if status_filter:
        conditions.append(SQLComplaint.status == status_filter)
    if category_filter:
        conditions.append(SQLComplaint.category == category_filter)
    if escalated_only:
        conditions.append(SQLComplaint.escalated == True)

    total = (await db.execute(select(func.count()).select_from(SQLComplaint).where(*conditions))).scalar()

    result = await db.execute(
        select(SQLComplaint)
        .where(*conditions)
        .order_by(SQLComplaint.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    complaints = [_sql_complaint_to_dict(c) for c in result.scalars().all()]
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


async def _get_all_complaints_mongo(db, page=1, limit=20, status_filter=None, category_filter=None, escalated_only=False):
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
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


# ---- Officer Complaints ----

async def get_officer_complaints(db, officer_id: str, page: int = 1, limit: int = 20, status_filter=None):
    if settings.use_supabase:
        return await _get_officer_complaints_sql(db, officer_id, page, limit, status_filter)
    return await _get_officer_complaints_mongo(db, officer_id, page, limit, status_filter)


async def _get_officer_complaints_sql(db, officer_id: str, page=1, limit=20, status_filter=None):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, func
    from app.services.user_service import get_user_by_id
    import uuid

    officer = await get_user_by_id(db, officer_id)
    if not officer:
        return {"complaints": [], "total": 0, "page": page, "pages": 0}

    conditions = []
    role = officer.get("role")

    if role == "local_officer" and officer.get("assigned_area_id"):
        conditions.append(SQLComplaint.area_id == uuid.UUID(officer["assigned_area_id"]))
    elif role == "zonal_officer" and officer.get("assigned_zone"):
        conditions.append(SQLComplaint.zone == officer["assigned_zone"])
    elif role == "district_officer":
        pass  # See all
    else:
        conditions.append(SQLComplaint.assigned_to == uuid.UUID(officer_id))

    if status_filter:
        conditions.append(SQLComplaint.status == status_filter)

    total = (await db.execute(select(func.count()).select_from(SQLComplaint).where(*conditions))).scalar()

    result = await db.execute(
        select(SQLComplaint)
        .where(*conditions)
        .order_by(SQLComplaint.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    complaints = [_sql_complaint_to_dict(c) for c in result.scalars().all()]
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


async def _get_officer_complaints_mongo(db, officer_id: str, page=1, limit=20, status_filter=None):
    from bson import ObjectId

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
        pass
    else:
        query["assigned_to"] = officer_id

    if status_filter:
        query["status"] = status_filter

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)
    cursor = db.complaints.find(query).skip(skip).limit(limit).sort("created_at", -1)
    complaints = await cursor.to_list(length=limit)
    return {"complaints": complaints, "total": total, "page": page, "pages": (total + limit - 1) // limit}


# ---- Status & Assignment ----

async def update_complaint_status(db, complaint_id: str, status: ComplaintStatus, resolution_notes=None):
    if settings.use_supabase:
        return await _update_complaint_status_sql(db, complaint_id, status, resolution_notes)
    return await _update_complaint_status_mongo(db, complaint_id, status, resolution_notes)


async def _update_complaint_status_sql(db, complaint_id: str, status: ComplaintStatus, resolution_notes=None):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select
    import uuid

    result = await db.execute(select(SQLComplaint).where(SQLComplaint.id == uuid.UUID(complaint_id)))
    complaint = result.scalar_one_or_none()
    if not complaint:
        return False

    complaint.status = status
    complaint.updated_at = datetime.utcnow()
    if status == ComplaintStatus.RESOLVED:
        complaint.resolved_at = datetime.utcnow()
    if resolution_notes:
        complaint.resolution_notes = resolution_notes

    await db.commit()

    if status == ComplaintStatus.RESOLVED and complaint.submitted_by:
        try:
            from app.tasks.notification import send_resolution_notification
            send_resolution_notification.delay(
                str(complaint.submitted_by), complaint_id,
                complaint.ticket_id, resolution_notes or ""
            )
        except Exception:
            pass

    return True


async def _update_complaint_status_mongo(db, complaint_id: str, status: ComplaintStatus, resolution_notes=None):
    from bson import ObjectId

    update_data = {"status": status, "updated_at": datetime.utcnow()}
    if status == ComplaintStatus.RESOLVED:
        update_data["resolved_at"] = datetime.utcnow()
    if resolution_notes:
        update_data["resolution_notes"] = resolution_notes

    result = await db.complaints.update_one({"_id": ObjectId(complaint_id)}, {"$set": update_data})

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
    if settings.use_supabase:
        return await _assign_complaint_sql(db, complaint_id, officer_id)
    return await _assign_complaint_mongo(db, complaint_id, officer_id)


async def _assign_complaint_sql(db, complaint_id: str, officer_id: str):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select
    import uuid

    result = await db.execute(select(SQLComplaint).where(SQLComplaint.id == uuid.UUID(complaint_id)))
    complaint = result.scalar_one_or_none()
    if not complaint:
        return False

    now = datetime.utcnow()
    complaint.assigned_to = uuid.UUID(officer_id)
    complaint.status = ComplaintStatus.IN_PROGRESS
    complaint.assigned_at = now
    complaint.updated_at = now
    await db.commit()

    try:
        from app.tasks.notification import send_assignment_notification
        send_assignment_notification.delay(officer_id, complaint_id, complaint.ticket_id)
    except Exception:
        pass

    return True


async def _assign_complaint_mongo(db, complaint_id: str, officer_id: str):
    from bson import ObjectId

    now = datetime.utcnow()
    update_data = {
        "assigned_to": officer_id,
        "status": ComplaintStatus.IN_PROGRESS,
        "assigned_at": now,
        "updated_at": now,
    }
    result = await db.complaints.update_one({"_id": ObjectId(complaint_id)}, {"$set": update_data})

    if result.modified_count > 0:
        complaint = await get_complaint_by_id(db, complaint_id)
        if complaint:
            try:
                from app.tasks.notification import send_assignment_notification
                send_assignment_notification.delay(officer_id, complaint_id, complaint["ticket_id"])
            except Exception:
                pass

    return result.modified_count > 0


# ---- Escalation ----

async def escalate_complaints(db) -> dict:
    if settings.use_supabase:
        return await _escalate_complaints_sql(db)
    return await _escalate_complaints_mongo(db)


async def _escalate_complaints_sql(db):
    from app.models.sql_models import SQLComplaint, SQLUser
    from sqlalchemy import select
    import uuid

    now = datetime.utcnow()
    stats = {"level1_escalated": 0, "level2_escalated": 0}
    level1_threshold = now - timedelta(days=settings.escalation_level1_days)
    level2_threshold = now - timedelta(days=settings.escalation_level2_days)

    # Level 0 -> Level 1
    result = await db.execute(
        select(SQLComplaint).where(
            SQLComplaint.status.in_([ComplaintStatus.IN_PROGRESS, ComplaintStatus.PENDING]),
            SQLComplaint.escalation_level == 0,
            SQLComplaint.assigned_at < level1_threshold,
            SQLComplaint.assigned_at.isnot(None),
            SQLComplaint.escalated == False,
        )
    )
    for complaint in result.scalars().all():
        zone = complaint.zone
        if not zone:
            await _escalate_to_district_officer_sql(db, complaint, now)
            stats["level2_escalated"] += 1
            continue

        zonal_result = await db.execute(
            select(SQLUser).where(
                SQLUser.role == UserRole.ZONAL_OFFICER,
                SQLUser.assigned_zone == zone,
                SQLUser.is_active == True,
            )
        )
        zonal_officer = zonal_result.scalar_one_or_none()

        if zonal_officer:
            complaint.escalated = True
            complaint.status = ComplaintStatus.ESCALATED
            complaint.escalation_level = 1
            complaint.escalated_to = zonal_officer.id
            complaint.assigned_to = zonal_officer.id
            complaint.assigned_at = now
            complaint.escalated_at = now
            complaint.updated_at = now
            await db.commit()

            try:
                from app.tasks.notification import send_escalation_notification
                send_escalation_notification.delay(str(zonal_officer.id), str(complaint.id), complaint.ticket_id, 1)
            except Exception:
                pass
            stats["level1_escalated"] += 1

    # Level 1 -> Level 2
    result = await db.execute(
        select(SQLComplaint).where(
            SQLComplaint.status == ComplaintStatus.ESCALATED,
            SQLComplaint.escalation_level == 1,
            SQLComplaint.assigned_at < level2_threshold,
        )
    )
    for complaint in result.scalars().all():
        await _escalate_to_district_officer_sql(db, complaint, now)
        stats["level2_escalated"] += 1

    # Unassigned old complaints
    result = await db.execute(
        select(SQLComplaint).where(
            SQLComplaint.status == ComplaintStatus.PENDING,
            SQLComplaint.assigned_to.is_(None),
            SQLComplaint.created_at < level1_threshold,
        )
    )
    for complaint in result.scalars().all():
        await _escalate_to_district_officer_sql(db, complaint, now)
        stats["level2_escalated"] += 1

    return stats


async def _escalate_to_district_officer_sql(db, complaint, now: datetime):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select

    result = await db.execute(
        select(SQLUser).where(SQLUser.role == UserRole.DISTRICT_OFFICER, SQLUser.is_active == True)
    )
    district_officer = result.scalar_one_or_none()

    district_id = district_officer.id if district_officer else None
    if district_id:
        complaint.escalated = True
        complaint.status = ComplaintStatus.ESCALATED
        complaint.escalation_level = 2
        complaint.escalated_to = district_id
        complaint.assigned_to = district_id
        complaint.assigned_at = now
        complaint.escalated_at = now
        complaint.updated_at = now
        await db.commit()

        try:
            from app.tasks.notification import send_escalation_notification
            send_escalation_notification.delay(str(district_id), str(complaint.id), complaint.ticket_id, 2)
        except Exception:
            pass


async def _escalate_complaints_mongo(db):
    from bson import ObjectId

    now = datetime.utcnow()
    stats = {"level1_escalated": 0, "level2_escalated": 0}
    level1_threshold = now - timedelta(days=settings.escalation_level1_days)
    level2_threshold = now - timedelta(days=settings.escalation_level2_days)

    # Level 0 -> Level 1
    complaints_for_level1 = await db.complaints.find({
        "status": {"$in": [ComplaintStatus.IN_PROGRESS, ComplaintStatus.PENDING]},
        "escalation_level": 0,
        "assigned_at": {"$lt": level1_threshold, "$ne": None},
        "escalated": False,
    }).to_list(length=500)

    for complaint in complaints_for_level1:
        zone = complaint.get("zone")
        if not zone:
            await _escalate_to_district_officer_mongo(db, complaint, now)
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

    # Level 1 -> Level 2
    complaints_for_level2 = await db.complaints.find({
        "status": ComplaintStatus.ESCALATED,
        "escalation_level": 1,
        "assigned_at": {"$lt": level2_threshold},
    }).to_list(length=500)

    for complaint in complaints_for_level2:
        await _escalate_to_district_officer_mongo(db, complaint, now)
        stats["level2_escalated"] += 1

    # Unassigned old
    unassigned_old = await db.complaints.find({
        "status": ComplaintStatus.PENDING,
        "assigned_to": None,
        "created_at": {"$lt": level1_threshold},
    }).to_list(length=200)

    for complaint in unassigned_old:
        await _escalate_to_district_officer_mongo(db, complaint, now)
        stats["level2_escalated"] += 1

    return stats


async def _escalate_to_district_officer_mongo(db, complaint: dict, now: datetime):
    from bson import ObjectId

    district_officer = await db.users.find_one({
        "role": UserRole.DISTRICT_OFFICER, "is_active": True,
    })

    district_id = str(district_officer["_id"]) if district_officer else None

    if district_id:
        await db.complaints.update_one(
            {"_id": complaint["_id"]},
            {"$set": {
                "escalated": True,
                "status": ComplaintStatus.ESCALATED,
                "escalation_level": 2,
                "escalated_to": district_id,
                "assigned_to": district_id,
                "assigned_at": now,
                "escalated_at": now,
                "updated_at": now,
            }},
        )
        try:
            from app.tasks.notification import send_escalation_notification
            send_escalation_notification.delay(district_id, str(complaint["_id"]), complaint["ticket_id"], 2)
        except Exception:
            pass


# ---- Geospatial & Stats ----

async def get_nearby_complaints(db, longitude: float, latitude: float, radius_km: float = 5):
    if settings.use_supabase:
        return await _get_nearby_complaints_sql(db, longitude, latitude, radius_km)
    return await _get_nearby_complaints_mongo(db, longitude, latitude, radius_km)


async def _get_nearby_complaints_sql(db, longitude: float, latitude: float, radius_km: float = 5):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, text

    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    result = await db.execute(
        select(SQLComplaint).where(
            SQLComplaint.location.isnot(None),
            text(f"ST_DWithin(location, ST_GeomFromText('{point_wkt}'), {radius_km * 1000})")
        ).order_by(text(f"location <-> ST_GeomFromText('{point_wkt}')")).limit(50)
    )
    return [_sql_complaint_to_dict(c) for c in result.scalars().all()]


async def _get_nearby_complaints_mongo(db, longitude: float, latitude: float, radius_km: float = 5):
    complaints = await db.complaints.find({
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": radius_km * 1000,
            }
        }
    }).to_list(length=50)
    return complaints


async def get_dashboard_stats(db):
    if settings.use_supabase:
        return await _get_dashboard_stats_sql(db)
    return await _get_dashboard_stats_mongo(db)


async def _get_dashboard_stats_sql(db):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, func, case

    total = (await db.execute(select(func.count()).select_from(SQLComplaint))).scalar()
    pending = (await db.execute(select(func.count()).select_from(SQLComplaint).where(SQLComplaint.status == ComplaintStatus.PENDING))).scalar()
    in_progress = (await db.execute(select(func.count()).select_from(SQLComplaint).where(SQLComplaint.status == ComplaintStatus.IN_PROGRESS))).scalar()
    resolved = (await db.execute(select(func.count()).select_from(SQLComplaint).where(SQLComplaint.status == ComplaintStatus.RESOLVED))).scalar()
    escalated = (await db.execute(select(func.count()).select_from(SQLComplaint).where(SQLComplaint.escalated == True))).scalar()
    resolution_rate = (resolved / total * 100) if total > 0 else 0

    avg_result = await db.execute(
        select(func.avg(
            func.extract('epoch', SQLComplaint.resolved_at - SQLComplaint.created_at) / 3600
        )).where(
            SQLComplaint.status == ComplaintStatus.RESOLVED,
            SQLComplaint.resolved_at.isnot(None),
        )
    )
    avg_hours = avg_result.scalar()

    return {
        "total_complaints": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "escalated": escalated,
        "resolution_rate": round(resolution_rate, 1),
        "avg_resolution_time_hours": round(avg_hours, 1) if avg_hours else None,
    }


async def _get_dashboard_stats_mongo(db):
    total = await db.complaints.count_documents({})
    pending = await db.complaints.count_documents({"status": ComplaintStatus.PENDING})
    in_progress = await db.complaints.count_documents({"status": ComplaintStatus.IN_PROGRESS})
    resolved = await db.complaints.count_documents({"status": ComplaintStatus.RESOLVED})
    escalated = await db.complaints.count_documents({"escalated": True})
    resolution_rate = (resolved / total * 100) if total > 0 else 0

    pipeline = [
        {"$match": {"status": ComplaintStatus.RESOLVED, "resolved_at": {"$ne": None}}},
        {"$project": {"resolution_time": {"$subtract": ["$resolved_at", "$created_at"]}}},
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
    if settings.use_supabase:
        return await _get_category_stats_sql(db)
    return await _get_category_stats_mongo(db)


async def _get_category_stats_sql(db):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select, func

    result = await db.execute(
        select(SQLComplaint.category, func.count().label("count"))
        .group_by(SQLComplaint.category)
        .order_by(func.count().desc())
    )
    return [{"category": row[0].value if row[0] else None, "count": row[1]} for row in result.all()]


async def _get_category_stats_mongo(db):
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    result = await db.complaints.aggregate(pipeline).to_list(length=20)
    return [{"category": r["_id"], "count": r["count"]} for r in result]


async def add_complaint_images(db, complaint_id: str, image_urls: list):
    if settings.use_supabase:
        return await _add_complaint_images_sql(db, complaint_id, image_urls)
    return await _add_complaint_images_mongo(db, complaint_id, image_urls)


async def _add_complaint_images_sql(db, complaint_id: str, image_urls: list):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select
    import uuid

    result = await db.execute(select(SQLComplaint).where(SQLComplaint.id == uuid.UUID(complaint_id)))
    complaint = result.scalar_one_or_none()
    if complaint:
        complaint.images = (complaint.images or []) + image_urls
        await db.commit()


async def _add_complaint_images_mongo(db, complaint_id: str, image_urls: list):
    from bson import ObjectId
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"images": {"$each": image_urls}}},
    )


async def add_resolution_images(db, complaint_id: str, image_urls: list):
    if settings.use_supabase:
        return await _add_resolution_images_sql(db, complaint_id, image_urls)
    return await _add_resolution_images_mongo(db, complaint_id, image_urls)


async def _add_resolution_images_sql(db, complaint_id: str, image_urls: list):
    from app.models.sql_models import SQLComplaint
    from sqlalchemy import select
    import uuid

    result = await db.execute(select(SQLComplaint).where(SQLComplaint.id == uuid.UUID(complaint_id)))
    complaint = result.scalar_one_or_none()
    if complaint:
        complaint.resolution_images = image_urls
        complaint.updated_at = datetime.utcnow()
        await db.commit()


async def _add_resolution_images_mongo(db, complaint_id: str, image_urls: list):
    from bson import ObjectId
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$set": {"resolution_images": image_urls, "updated_at": datetime.utcnow()}},
    )
