from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AreaResponse(BaseModel):
    id: str
    name: str
    ward_number: int
    zone: str
    district: str
    boundary: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AreaListResponse(BaseModel):
    areas: list[AreaResponse]
    total: int
