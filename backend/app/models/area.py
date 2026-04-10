from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Area(BaseModel):
    id: str = Field(alias="_id")
    name: str
    ward_number: int
    zone: str
    district: str
    boundary: Optional[dict] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class AreaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    ward_number: int = Field(..., ge=1)
    zone: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    boundary: Optional[dict] = None


class AreaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    ward_number: Optional[int] = Field(None, ge=1)
    zone: Optional[str] = Field(None, min_length=1, max_length=100)
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    boundary: Optional[dict] = None
    is_active: Optional[bool] = None
