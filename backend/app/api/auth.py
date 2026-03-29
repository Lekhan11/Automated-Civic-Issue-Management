from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_active_user
from app.schemas.user import (
    UserCreateRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: UserCreateRequest, db=Depends(get_db)):
    try:
        user = await user_service.create_user(db, request.model_dump())
        return {
            "message": "User registered successfully",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user["name"],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db=Depends(get_db)):
    user = await user_service.get_user_by_email(db, request.email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": user["email"], "role": user["role"]})

    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_active_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user["name"],
        phone=current_user.get("phone"),
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
    )


@router.put("/me")
async def update_me(
    request: UserUpdateRequest,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    user = await user_service.update_user(db, str(current_user["_id"]), update_data)
    return {"message": "Profile updated successfully"}
