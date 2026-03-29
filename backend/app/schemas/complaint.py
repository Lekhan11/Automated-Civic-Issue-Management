from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.complaint import ComplaintCategory, ComplaintStatus, Priority


class LocationSchema(BaseModel):
    type: str = "Point"
    coordinates: List[float]


class ComplaintCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ComplaintCategory
    latitude: float
    longitude: float
    address: Optional[str] = None


class ComplaintUpdateRequest(BaseModel):
    status: Optional[ComplaintStatus] = None
    resolution_notes: Optional[str] = None


class AssignOfficerRequest(BaseModel):
    officer_id: str


class ComplaintResponse(BaseModel):
    id: str
    ticket_id: str
    title: str
    description: str
    category: ComplaintCategory
    status: ComplaintStatus
    priority: Priority
    location: LocationSchema
    address: Optional[str] = None
    images: List[str] = []
    submitted_by: str
    submitted_by_name: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    escalated: bool
    escalation_level: int
    resolution_notes: Optional[str] = None
    resolution_images: List[str] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplaintListResponse(BaseModel):
    complaints: List[ComplaintResponse]
    total: int
    page: int
    pages: int


class DashboardStats(BaseModel):
    total_complaints: int
    pending: int
    in_progress: int
    resolved: int
    escalated: int
    resolution_rate: float
    avg_resolution_time_hours: Optional[float]


class CategoryStats(BaseModel):
    category: str
    count: int
