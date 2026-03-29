from datetime import datetime
from bson import ObjectId
from app.core.security import get_password_hash
from app.models.user import UserRole


async def create_user(db, user_data: dict) -> dict:
    existing = await db.users.find_one({"email": user_data["email"]})
    if existing:
        raise ValueError("Email already registered")

    user_doc = {
        "email": user_data["email"],
        "name": user_data["name"],
        "phone": user_data.get("phone"),
        "hashed_password": get_password_hash(user_data["password"]),
        "role": user_data.get("role", UserRole.USER),
        "is_active": True,
        "assigned_area": user_data.get("assigned_area"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


async def get_user_by_email(db, email: str):
    return await db.users.find_one({"email": email})


async def get_user_by_id(db, user_id: str):
    try:
        return await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


async def get_all_officers(db):
    cursor = db.users.find(
        {"role": {"$in": [UserRole.LOCAL_OFFICER, UserRole.SUPER_ADMIN]}}
    )
    officers = await cursor.to_list(length=100)
    return officers


async def update_user(db, user_id: str, update_data: dict):
    update_data["updated_at"] = datetime.utcnow()
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
    )
    if result.modified_count == 0:
        raise ValueError("User not found or no changes made")
    return await get_user_by_id(db, user_id)


async def get_all_users(db, page: int = 1, limit: int = 20):
    skip = (page - 1) * limit
    total = await db.users.count_documents({})
    cursor = db.users.find({}).skip(skip).limit(limit).sort("created_at", -1)
    users = await cursor.to_list(length=limit)
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }
