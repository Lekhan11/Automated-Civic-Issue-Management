from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ComplaintCategory(str, Enum):
    ENCROACHMENT = "encroachment"
    GARBAGE_DUMP = "garbage_dump"
    ROAD_DAMAGE = "road_damage"
    WATER_ISSUE = "water_issue"
    DRAINAGE = "drainage"
    STREET_LIGHT = "street_light"
    OTHER = "other"


class ComplaintStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=2)  # [longitude, latitude]


class ComplaintBase(BaseModel):
    title: str
    description: str
    category: ComplaintCategory


class ComplaintCreate(ComplaintBase):
    location: Location
    address: Optional[str] = None
    images: List[str] = []  # Cloudinary URLs


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_images: List[str] = []


class ComplaintInDB(ComplaintBase):
    id: str = Field(alias="_id")
    ticket_id: str
    location: Location
    address: Optional[str] = None
    images: List[str] = []
    status: ComplaintStatus = ComplaintStatus.PENDING
    priority: Priority = Priority.MEDIUM
    submitted_by: str  # User ID
    assigned_to: Optional[str] = None
    escalated: bool = False
    escalated_to: Optional[str] = None
    escalation_level: int = 0
    area_id: Optional[str] = None
    ward_number: Optional[int] = None
    zone: Optional[str] = None
    district: Optional[str] = None
    geocoded_area_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolution_images: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class Complaint(ComplaintBase):
    id: str = Field(alias="_id")
    ticket_id: str
    location: Location
    address: Optional[str] = None
    images: List[str] = []
    status: ComplaintStatus
    priority: Priority
    submitted_by: str
    assigned_to: Optional[str] = None
    escalated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class ComplaintList(BaseModel):
    complaints: List[Complaint]
    total: int
    page: int
    pages: int