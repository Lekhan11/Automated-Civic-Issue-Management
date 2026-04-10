from datetime import datetime
from bson import ObjectId


async def create_area(db, area_data: dict) -> dict:
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
    try:
        return await db.areas.find_one({"_id": ObjectId(area_id), "is_active": True})
    except Exception:
        return None


async def get_area_by_name(db, name: str):
    """Case-insensitive match on area name."""
    return await db.areas.find_one({
        "name": {"$regex": f"^{name}$", "$options": "i"},
        "is_active": True,
    })


async def get_all_areas(db, page: int = 1, limit: int = 50, zone: str = None, district: str = None):
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


async def update_area(db, area_id: str, update_data: dict) -> dict:
    update_data["updated_at"] = datetime.utcnow()
    result = await db.areas.update_one(
        {"_id": ObjectId(area_id)},
        {"$set": update_data},
    )
    if result.modified_count == 0:
        raise ValueError("Area not found or no changes made")
    return await get_area_by_id(db, area_id)


async def delete_area(db, area_id: str) -> bool:
    result = await db.areas.update_one(
        {"_id": ObjectId(area_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
    )
    return result.modified_count > 0


async def get_zones(db, district: str = None) -> list[str]:
    """Return distinct active zone values, optionally filtered by district."""
    query = {"is_active": True}
    if district:
        query["district"] = district
    zones = await db.areas.distinct("zone", query)
    return sorted(zones)


async def get_districts(db) -> list[str]:
    """Return distinct active district values."""
    districts = await db.areas.distinct("district", {"is_active": True})
    return sorted(districts)
