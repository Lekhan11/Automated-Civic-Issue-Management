from datetime import datetime
from app.core.config import settings


async def create_area(db, area_data: dict) -> dict:
    if settings.use_supabase:
        return await _create_area_sql(db, area_data)
    return await _create_area_mongo(db, area_data)


async def _create_area_sql(db, area_data: dict) -> dict:
    from app.models.sql_models import SQLArea
    import uuid

    area = SQLArea(
        id=uuid.uuid4(),
        name=area_data["name"],
        ward_number=area_data["ward_number"],
        zone=area_data["zone"],
        district=area_data["district"],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return _sql_area_to_dict(area)


async def _create_area_mongo(db, area_data: dict) -> dict:
    from bson import ObjectId

    area_doc = {
        "name": area_data["name"],
        "ward_number": area_data["ward_number"],
        "zone": area_data["zone"],
        "district": area_data["district"],
        "boundary": area_data.get("boundary"),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.areas.insert_one(area_doc)
    area_doc["_id"] = result.inserted_id
    return area_doc


async def get_area_by_id(db, area_id: str):
    if settings.use_supabase:
        return await _get_area_by_id_sql(db, area_id)
    return await _get_area_by_id_mongo(db, area_id)


async def _get_area_by_id_sql(db, area_id: str):
    from app.models.sql_models import SQLArea
    import uuid
    from sqlalchemy import select

    try:
        result = await db.execute(
            select(SQLArea).where(SQLArea.id == uuid.UUID(area_id), SQLArea.is_active == True)
        )
        area = result.scalar_one_or_none()
        return _sql_area_to_dict(area) if area else None
    except (ValueError, Exception):
        return None


async def _get_area_by_id_mongo(db, area_id: str):
    from bson import ObjectId
    try:
        return await db.areas.find_one({"_id": ObjectId(area_id), "is_active": True})
    except Exception:
        return None


async def get_area_by_name(db, name: str):
    if settings.use_supabase:
        return await _get_area_by_name_sql(db, name)
    return await _get_area_by_name_mongo(db, name)


async def _get_area_by_name_sql(db, name: str):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select

    result = await db.execute(
        select(SQLArea).where(SQLArea.name.ilike(name), SQLArea.is_active == True)
    )
    area = result.scalar_one_or_none()
    return _sql_area_to_dict(area) if area else None


async def _get_area_by_name_mongo(db, name: str):
    return await db.areas.find_one({
        "name": {"$regex": f"^{name}$", "$options": "i"},
        "is_active": True,
    })


async def get_all_areas(db, page: int = 1, limit: int = 50, zone: str = None, district: str = None):
    if settings.use_supabase:
        return await _get_all_areas_sql(db, page, limit, zone, district)
    return await _get_all_areas_mongo(db, page, limit, zone, district)


async def _get_all_areas_sql(db, page: int = 1, limit: int = 50, zone: str = None, district: str = None):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select, func

    conditions = [SQLArea.is_active == True]
    if zone:
        conditions.append(SQLArea.zone == zone)
    if district:
        conditions.append(SQLArea.district == district)

    count_q = select(func.count()).select_from(SQLArea).where(*conditions)
    total = (await db.execute(count_q)).scalar()

    query = (
        select(SQLArea)
        .where(*conditions)
        .order_by(SQLArea.district, SQLArea.zone)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    areas = [_sql_area_to_dict(a) for a in result.scalars().all()]
    return {
        "areas": areas,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def _get_all_areas_mongo(db, page: int = 1, limit: int = 50, zone: str = None, district: str = None):
    query = {"is_active": True}
    if zone:
        query["zone"] = zone
    if district:
        query["district"] = district

    skip = (page - 1) * limit
    total = await db.areas.count_documents(query)
    cursor = db.areas.find(query).skip(skip).limit(limit).sort("district", 1).sort("zone", 1)
    areas = await cursor.to_list(length=limit)
    return {
        "areas": areas,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def get_nearby_areas(db, latitude: float, longitude: float, limit: int = 5) -> list:
    """Get nearest areas by geospatial distance."""
    if settings.use_supabase:
        return await _get_nearby_areas_sql(db, latitude, longitude, limit)
    return await _get_nearby_areas_mongo(db, latitude, longitude, limit)


async def _get_nearby_areas_sql(db, latitude: float, longitude: float, limit: int = 5):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select, text
    from sqlalchemy.orm import load_only
    from geoalchemy2.functions import ST_MakePoint, ST_SetSRID

    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    query = (
        select(SQLArea)
        .where(
            SQLArea.is_active == True,
            SQLArea.location.isnot(None),
            text(f"ST_DWithin(location, ST_GeomFromText('{point_wkt}'), 50000)")
        )
        .order_by(text(f"location <-> ST_GeomFromText('{point_wkt}')"))
        .limit(limit)
    )
    result = await db.execute(query)
    return [_sql_area_to_dict(a) for a in result.scalars().all()]


async def _get_nearby_areas_mongo(db, latitude: float, longitude: float, limit: int = 5):
    try:
        cursor = db.areas.find({
            "is_active": True,
            "location": {"$near": {
                "$geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "$maxDistance": 50000,
            }},
        }).limit(limit)
        return [area async for area in cursor]
    except Exception:
        return []


async def find_areas_by_name_regex(db, name: str, zone: str = None) -> list:
    """Find areas with partial name match (for area resolution fallback)."""
    if settings.use_supabase:
        return await _find_areas_by_name_regex_sql(db, name, zone)
    return await _find_areas_by_name_regex_mongo(db, name, zone)


async def _find_areas_by_name_regex_sql(db, name: str, zone: str = None):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select

    conditions = [SQLArea.is_active == True, SQLArea.name.ilike(f"%{name}%")]
    if zone:
        conditions.append(SQLArea.zone.ilike(f"%{zone}%"))

    result = await db.execute(select(SQLArea).where(*conditions))
    return [_sql_area_to_dict(a) for a in result.scalars().all()]


async def _find_areas_by_name_regex_mongo(db, name: str, zone: str = None):
    query = {
        "name": {"$regex": name, "$options": "i"},
        "is_active": True,
    }
    if zone:
        query["zone"] = {"$regex": zone, "$options": "i"}
    cursor = db.areas.find(query)
    return [area async for area in cursor]


async def update_area(db, area_id: str, update_data: dict) -> dict:
    if settings.use_supabase:
        return await _update_area_sql(db, area_id, update_data)
    return await _update_area_mongo(db, area_id, update_data)


async def _update_area_sql(db, area_id: str, update_data: dict) -> dict:
    from app.models.sql_models import SQLArea
    import uuid

    result = await db.execute(
        select(SQLArea).where(SQLArea.id == uuid.UUID(area_id))
    )
    area = result.scalar_one_or_none()
    if not area:
        raise ValueError("Area not found")

    for key, value in update_data.items():
        if hasattr(area, key):
            setattr(area, key, value)
    area.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(area)
    return _sql_area_to_dict(area)


async def _update_area_mongo(db, area_id: str, update_data: dict) -> dict:
    from bson import ObjectId

    update_data["updated_at"] = datetime.utcnow()
    result = await db.areas.update_one(
        {"_id": ObjectId(area_id)},
        {"$set": update_data},
    )
    if result.modified_count == 0:
        raise ValueError("Area not found or no changes made")
    return await get_area_by_id(db, area_id)


async def delete_area(db, area_id: str) -> bool:
    if settings.use_supabase:
        return await _delete_area_sql(db, area_id)
    return await _delete_area_mongo(db, area_id)


async def _delete_area_sql(db, area_id: str) -> bool:
    from app.models.sql_models import SQLArea
    import uuid

    result = await db.execute(
        select(SQLArea).where(SQLArea.id == uuid.UUID(area_id))
    )
    area = result.scalar_one_or_none()
    if not area:
        return False
    area.is_active = False
    area.updated_at = datetime.utcnow()
    await db.commit()
    return True


async def _delete_area_mongo(db, area_id: str) -> bool:
    from bson import ObjectId

    result = await db.areas.update_one(
        {"_id": ObjectId(area_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
    )
    return result.modified_count > 0


async def get_zones(db, district: str = None) -> list:
    if settings.use_supabase:
        return await _get_zones_sql(db, district)
    return await _get_zones_mongo(db, district)


async def _get_zones_sql(db, district: str = None):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select, distinct

    query = select(distinct(SQLArea.zone)).where(SQLArea.is_active == True)
    if district:
        query = query.where(SQLArea.district == district)
    result = await db.execute(query.order_by(SQLArea.zone))
    return [row[0] for row in result.all()]


async def _get_zones_mongo(db, district: str = None):
    query = {"is_active": True}
    if district:
        query["district"] = district
    zones = await db.areas.distinct("zone", query)
    return sorted(zones)


async def get_districts(db) -> list:
    if settings.use_supabase:
        return await _get_districts_sql(db)
    return await _get_districts_mongo(db)


async def _get_districts_sql(db):
    from app.models.sql_models import SQLArea
    from sqlalchemy import select, distinct

    result = await db.execute(
        select(distinct(SQLArea.district))
        .where(SQLArea.is_active == True)
        .order_by(SQLArea.district)
    )
    return [row[0] for row in result.all()]


async def _get_districts_mongo(db):
    districts = await db.areas.distinct("district", {"is_active": True})
    return sorted(districts)


async def get_area_count(db) -> int:
    if settings.use_supabase:
        from app.models.sql_models import SQLArea
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(SQLArea).where(SQLArea.is_active == True))
        return result.scalar()
    return await db.areas.count_documents({"is_active": True})


def _sql_area_to_dict(area) -> dict:
    from sqlalchemy.inspection import inspect

    if area is None:
        return None
    data = {}
    mapper = inspect(area).mapper
    for column in mapper.columns:
        value = getattr(area, column.key)
        if column.key == "location" and value is not None:
            from geoalchemy2.shape import to_shape
            shape = to_shape(value)
            data["location"] = {
                "type": "Point",
                "coordinates": [shape.x, shape.y],
            }
            data["latitude"] = shape.y
            data["longitude"] = shape.x
        else:
            data[column.key] = value
    data["_id"] = str(data["id"])
    return data
