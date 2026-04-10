from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole
from app.models.complaint import ComplaintStatus, ComplaintCategory
from app.schemas.complaint import ComplaintResponse, ComplaintListResponse, DashboardStats, CategoryStats
from app.schemas.user import UserResponse, OfficerCreateRequest
from app.services import complaint_service, user_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ---- Complaint Management ----

@router.get("/complaints", response_model=ComplaintListResponse)
async def get_all_complaints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    escalated_only: bool = False,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    # Convert string to enum, treating empty strings as None
    status_filter = None
    if status and status.strip():
        try:
            status_filter = ComplaintStatus(status.strip())
        except ValueError:
            pass  # Invalid status, ignore

    category_filter = None
    if category and category.strip():
        try:
            category_filter = ComplaintCategory(category.strip())
        except ValueError:
            pass  # Invalid category, ignore

    result = await complaint_service.get_all_complaints(
        db, page, limit, status_filter, category_filter, escalated_only
    )
    complaints = []
    for c in result["complaints"]:
        submitter = await user_service.get_user_by_id(db, c["submitted_by"])
        assignee = None
        if c.get("assigned_to"):
            assignee = await user_service.get_user_by_id(db, c["assigned_to"])
        complaints.append(ComplaintResponse(
            id=str(c["_id"]),
            submitted_by_name=submitter["name"] if submitter else None,
            assigned_to_name=assignee["name"] if assignee else None,
            **{k: v for k, v in c.items() if k != "_id"},
        ))
    return ComplaintListResponse(
        complaints=complaints,
        total=result["total"],
        page=result["page"],
        pages=result["pages"],
    )


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    stats = await complaint_service.get_dashboard_stats(db)
    return DashboardStats(**stats)


@router.get("/stats/categories", response_model=list[CategoryStats])
async def get_category_stats(
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    stats = await complaint_service.get_category_stats(db)
    return [CategoryStats(**s) for s in stats]


@router.put("/complaints/{complaint_id}/assign")
async def assign_complaint(
    complaint_id: str,
    officer_id: str,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    officer = await user_service.get_user_by_id(db, officer_id)
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")

    await complaint_service.assign_complaint(db, complaint_id, officer_id)
    return {"message": f"Complaint assigned to {officer['name']}"}


@router.put("/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    status: ComplaintStatus,
    resolution_notes: Optional[str] = None,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    complaint = await complaint_service.get_complaint_by_id(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    await complaint_service.update_complaint_status(
        db, complaint_id, status, resolution_notes
    )
    return {"message": "Complaint status updated"}


# ---- User Management ----

@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    result = await user_service.get_all_users(db, page, limit)
    users = [
        UserResponse(
            id=str(u["_id"]),
            email=u["email"],
            name=u["name"],
            phone=u.get("phone"),
            role=u["role"],
            is_active=u["is_active"],
            created_at=u["created_at"],
        )
        for u in result["users"]
    ]
    return {"users": users, "total": result["total"], "page": result["page"], "pages": result["pages"]}


@router.get("/officers")
async def get_officers(
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    officers = await user_service.get_all_officers(db)
    return [
        {
            "id": str(o["_id"]),
            "name": o["name"],
            "email": o["email"],
            "role": o["role"],
            "assigned_area_id": o.get("assigned_area_id"),
            "assigned_zone": o.get("assigned_zone"),
        }
        for o in officers
    ]


@router.post("/officers", status_code=201)
async def create_officer(
    request: OfficerCreateRequest,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    from app.models.user import UserRole
    data = request.model_dump()
    valid_roles = [UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER]
    requested_role = data.get("role", "local_officer")
    if requested_role not in [r.value for r in valid_roles]:
        data["role"] = UserRole.LOCAL_OFFICER
    else:
        data["role"] = UserRole(requested_role)
    try:
        user = await user_service.create_user(db, data)
        return {
            "message": "Officer created successfully",
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
