from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    LOCAL_OFFICER = "local_officer"
    ZONAL_OFFICER = "zonal_officer"
    DISTRICT_OFFICER = "district_officer"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str
    role: UserRole = UserRole.USER
    assigned_area_id: Optional[str] = None  # Reference to areas collection
    assigned_zone: Optional[str] = None  # For zonal_officer: zone name
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class User(UserBase):
    id: str = Field(alias="_id")
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime

    class Config:
        populate_by_name = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None