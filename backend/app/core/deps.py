from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.database import get_db
from app.core.config import settings
from app.models.user import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
):
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if settings.use_supabase:
        user = await _get_user_by_email_sql(db, email)
    else:
        user = await _get_user_by_email_mongo(db, email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def _get_user_by_email_sql(db, email: str):
    from app.models.sql_models import SQLUser
    from sqlalchemy import select
    result = await db.execute(select(SQLUser).where(SQLUser.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    data = {
        "id": str(user.id),
        "_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "hashed_password": user.hashed_password,
        "role": user.role.value if user.role else None,
        "is_active": user.is_active,
        "assigned_area_id": str(user.assigned_area_id) if user.assigned_area_id else None,
        "assigned_zone": user.assigned_zone,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }
    return data


async def _get_user_by_email_mongo(db, email: str):
    return await db.users.find_one({"email": email})


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*roles: UserRole):
    async def role_checker(current_user=Depends(get_current_active_user)):
        user_role = current_user.get("role")
        if user_role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join([r.value for r in roles])}",
            )
        return current_user
    return role_checker
