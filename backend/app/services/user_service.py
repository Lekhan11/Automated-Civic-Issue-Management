from datetime import datetime
from app.core.config import settings
from app.core.security import get_password_hash


async def create_user(db, user_data: dict) -> dict:
    if settings.use_supabase:
        return await _create_user_sql(db, user_data)
    return await _create_user_mongo(db, user_data)


async def _create_user_sql(db, user_data: dict) -> dict:
    from app.models.sql_models import SQLUser
    from app.models.user import UserRole
    import uuid

    existing = await get_user_by_email(db, user_data["email"])
    if existing:
        raise ValueError("Email already registered")

    user = SQLUser(
        id=uuid.uuid4(),
        email=user_data["email"],
        name=user_data["name"],
        phone=user_data.get("phone"),
        hashed_password=get_password_hash(user_data["password"]),
        role=UserRole(user_data.get("role", "user")),
        is_active=True,
        assigned_area_id=user_data.get("assigned_area_id"),
        assigned_zone=user_data.get("assigned_zone"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _sql_user_to_dict(user)


async def _create_user_mongo(db, user_data: dict) -> dict:
    from app.models.user import UserRole

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
        "assigned_area_id": user_data.get("assigned_area_id"),
        "assigned_zone": user_data.get("assigned_zone"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


async def get_user_by_email(db, email: str):
    if settings.use_supabase:
        return await _get_user_by_email_sql(db, email)
    return await _get_user_by_email_mongo(db, email)


async def _get_user_by_email_sql(db, email: str):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select

    result = await db.execute(select(SQLUser).where(SQLUser.email == email))
    user = result.scalar_one_or_none()
    return _sql_user_to_dict(user) if user else None


async def _get_user_by_email_mongo(db, email: str):
    return await db.users.find_one({"email": email})


async def get_user_by_id(db, user_id: str):
    if settings.use_supabase:
        return await _get_user_by_id_sql(db, user_id)
    return await _get_user_by_id_mongo(db, user_id)


async def _get_user_by_id_sql(db, user_id: str):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select
    import uuid

    try:
        result = await db.execute(select(SQLUser).where(SQLUser.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        return _sql_user_to_dict(user) if user else None
    except (ValueError, Exception):
        return None


async def _get_user_by_id_mongo(db, user_id: str):
    from bson import ObjectId
    try:
        return await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


async def get_all_officers(db):
    if settings.use_supabase:
        return await _get_all_officers_sql(db)
    return await _get_all_officers_mongo(db)


async def _get_all_officers_sql(db):
    from app.models.sql_models import SQLUser
    from app.models.user import UserRole
    from sqlalchemy import select

    result = await db.execute(
        select(SQLUser).where(
            SQLUser.role.in_([UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER])
        )
    )
    return [_sql_user_to_dict(u) for u in result.scalars().all()]


async def _get_all_officers_mongo(db):
    from app.models.user import UserRole

    cursor = db.users.find(
        {"role": {"$in": [UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER]}}
    )
    return [u async for u in cursor]


async def get_officers_by_area(db, area_id: str, role=None):
    if settings.use_supabase:
        return await _get_officers_by_area_sql(db, area_id, role)
    return await _get_officers_by_area_mongo(db, area_id, role)


async def _get_officers_by_area_sql(db, area_id: str, role=None):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select
    import uuid

    conditions = [SQLUser.assigned_area_id == uuid.UUID(area_id), SQLUser.is_active == True]
    if role:
        conditions.append(SQLUser.role == role)

    result = await db.execute(select(SQLUser).where(*conditions))
    return [_sql_user_to_dict(u) for u in result.scalars().all()]


async def _get_officers_by_area_mongo(db, area_id: str, role=None):
    query = {"assigned_area_id": area_id, "is_active": True}
    if role:
        query["role"] = role
    cursor = db.users.find(query)
    return [u async for u in cursor]


async def get_officers_by_zone(db, zone: str, role=None):
    if settings.use_supabase:
        return await _get_officers_by_zone_sql(db, zone, role)
    return await _get_officers_by_zone_mongo(db, zone, role)


async def _get_officers_by_zone_sql(db, zone: str, role=None):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select

    conditions = [SQLUser.assigned_zone == zone, SQLUser.is_active == True]
    if role:
        conditions.append(SQLUser.role == role)

    result = await db.execute(select(SQLUser).where(*conditions))
    return [_sql_user_to_dict(u) for u in result.scalars().all()]


async def _get_officers_by_zone_mongo(db, zone: str, role=None):
    query = {"assigned_zone": zone, "is_active": True}
    if role:
        query["role"] = role
    cursor = db.users.find(query)
    return [u async for u in cursor]


async def update_user(db, user_id: str, update_data: dict):
    if settings.use_supabase:
        return await _update_user_sql(db, user_id, update_data)
    return await _update_user_mongo(db, user_id, update_data)


async def _update_user_sql(db, user_id: str, update_data: dict) -> dict:
    from app.models.sql_models import SQLUser
    import uuid

    result = await db.execute(
        select(SQLUser).where(SQLUser.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return _sql_user_to_dict(user)


async def _update_user_mongo(db, user_id: str, update_data: dict) -> dict:
    from bson import ObjectId

    update_data["updated_at"] = datetime.utcnow()
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
    )
    if result.modified_count == 0:
        raise ValueError("User not found or no changes made")
    return await get_user_by_id(db, user_id)


async def get_all_users(db, page: int = 1, limit: int = 20):
    if settings.use_supabase:
        return await _get_all_users_sql(db, page, limit)
    return await _get_all_users_mongo(db, page, limit)


async def _get_all_users_sql(db, page: int = 1, limit: int = 20):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select, func

    count_q = select(func.count()).select_from(SQLUser)
    total = (await db.execute(count_q)).scalar()

    query = (
        select(SQLUser)
        .order_by(SQLUser.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    users = [_sql_user_to_dict(u) for u in result.scalars().all()]
    return {
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


async def _get_all_users_mongo(db, page: int = 1, limit: int = 20):
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


def _sql_user_to_dict(user) -> dict:
    from sqlalchemy.inspection import inspect

    if user is None:
        return None
    data = {}
    mapper = inspect(user).mapper
    for column in mapper.columns:
        value = getattr(user, column.key)
        if column.key == "role":
            data[column.key] = value.value if value else None
        else:
            data[column.key] = value
    data["_id"] = str(data["id"])
    return data
