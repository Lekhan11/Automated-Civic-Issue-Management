from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.user import UserRole
from app.models.complaint import ComplaintStatus, ComplaintCategory
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintUpdateRequest,
    ComplaintResponse,
    ComplaintListResponse,
    DashboardStats,
    CategoryStats,
    AssignOfficerRequest,
)
from app.services import complaint_service
from app.services.cloudinary_service import upload_images

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    request: ComplaintCreateRequest,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    complaint = await complaint_service.create_complaint(
        db, str(current_user["_id"]), request.model_dump()
    )
    return {
        "message": "Complaint submitted successfully",
        "ticket_id": complaint["ticket_id"],
        "complaint": ComplaintResponse(
            id=str(complaint["_id"]),
            **complaint,
        ),
    }


@router.post("/{complaint_id}/images")
async def upload_complaint_images(
    complaint_id: str,
    files: list[UploadFile] = File(...),
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    image_urls = await upload_images(files)
    await complaint_service.add_complaint_images(db, complaint_id, image_urls)

    return {"message": "Images uploaded successfully", "images": image_urls}


@router.post("/{complaint_id}/resolution-images")
async def upload_resolution_images(
    complaint_id: str,
    files: list[UploadFile] = File(...),
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    image_urls = await upload_images(files)
    await complaint_service.add_resolution_images(db, complaint_id, image_urls)
    return {"message": "Resolution images uploaded successfully", "images": image_urls}


@router.get("/my", response_model=ComplaintListResponse)
async def get_my_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ComplaintStatus] = None,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    result = await complaint_service.get_complaints_by_user(
        db, str(current_user["_id"]), page, limit, status
    )
    complaints = [
        ComplaintResponse(
            id=str(c["_id"]),
            submitted_by_name=None,
            assigned_to_name=None,
            **{k: v for k, v in c.items() if k != "_id"},
        )
        for c in result["complaints"]
    ]
    return ComplaintListResponse(
        complaints=complaints,
        total=result["total"],
        page=result["page"],
        pages=result["pages"],
    )


@router.get("/assigned", response_model=ComplaintListResponse)
async def get_assigned_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ComplaintStatus] = None,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get complaints assigned TO the current user (for officers)."""
    from app.services import user_service

    result = await complaint_service.get_officer_complaints(
        db, str(current_user["_id"]), page, limit
    )

    if status:
        result["complaints"] = [c for c in result["complaints"] if c.get("status") == status]
        result["total"] = len(result["complaints"])

    complaints = []
    for c in result["complaints"]:
        submitter = await user_service.get_user_by_id(db, c.get("submitted_by"))
        complaints.append(ComplaintResponse(
            id=str(c["_id"]),
            submitted_by_name=submitter["name"] if submitter else None,
            assigned_to_name=current_user["name"],
            **{k: v for k, v in c.items() if k != "_id"},
        ))

    return ComplaintListResponse(
        complaints=complaints,
        total=result["total"],
        page=result["page"],
        pages=max(1, (result["total"] + limit - 1) // limit),
    )


@router.get("/nearby")
async def get_nearby_complaints(
    longitude: float,
    latitude: float,
    radius: float = Query(5, ge=0.1, le=50),
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    complaints = await complaint_service.get_nearby_complaints(
        db, longitude, latitude, radius
    )
    return {"complaints": complaints}


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return ComplaintResponse(
        id=str(complaint["_id"]),
        submitted_by_name=None,
        assigned_to_name=None,
        **{k: v for k, v in complaint.items() if k != "_id"},
    )


@router.put("/{complaint_id}")
async def update_complaint(
    complaint_id: str,
    request: ComplaintUpdateRequest,
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # RBAC: Check if user can update this complaint
    user_role = current_user.get("role")
    user_id = str(current_user["_id"])
    can_update = False

    if user_role == "district_officer":
        can_update = True
    elif user_role == "zonal_officer":
        can_update = complaint.get("zone") == current_user.get("assigned_zone")
    elif user_role == "local_officer":
        can_update = complaint.get("area_id") == current_user.get("assigned_area_id")
    elif user_role == "user":
        can_update = complaint.get("submitted_by") == user_id

    if not can_update:
        raise HTTPException(status_code=403, detail="Not authorized to update this complaint")

    if request.status:
        updated = await complaint_service.update_complaint_status(
            db, complaint_id, request.status, request.resolution_notes
        )
        if not updated:
            raise HTTPException(status_code=400, detail="Failed to update complaint")
        return {"message": "Complaint updated successfully"}

    return {"message": "No changes made"}
