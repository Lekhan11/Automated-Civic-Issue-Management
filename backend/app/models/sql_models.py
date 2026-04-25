import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship
from geoalchemy2 import Geometry
from app.models.user import UserRole
from app.models.complaint import ComplaintStatus, ComplaintCategory, Priority


class Base(DeclarativeBase):
    pass


class SQLUser(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    assigned_area_id = Column(UUID(as_uuid=True), nullable=True)
    assigned_zone = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complaints = relationship("SQLComplaint", back_populates="submitter", foreign_keys="SQLComplaint.submitted_by")


class SQLComplaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(ComplaintCategory), nullable=False)
    status = Column(Enum(ComplaintStatus), nullable=False, default=ComplaintStatus.PENDING)
    priority = Column(Enum(Priority), nullable=False, default=Priority.MEDIUM)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    images = Column(ARRAY(String), default=list)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    area_id = Column(UUID(as_uuid=True), nullable=True)
    ward_number = Column(Integer, nullable=True)
    zone = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    area_name = Column(String(200), nullable=True)
    geocoded_area_name = Column(String(200), nullable=True)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(UUID(as_uuid=True), nullable=True)
    escalation_level = Column(Integer, default=0)
    resolution_notes = Column(Text, nullable=True)
    resolution_images = Column(ARRAY(String), default=list)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submitter = relationship("SQLUser", back_populates="complaints", foreign_keys=[submitted_by])


class SQLArea(Base):
    __tablename__ = "areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    ward_number = Column(Integer, nullable=False)
    zone = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    boundary = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
