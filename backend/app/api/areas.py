from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db
from app.core.deps import require_role, get_current_active_user
from app.models.user import UserRole
from app.schemas.area import AreaResponse, AreaListResponse
from app.models.area import AreaCreate, AreaUpdate
from app.services import area_service, complaint_service

router = APIRouter(prefix="/api/admin/areas", tags=["Areas"])


@router.post("/", response_model=AreaResponse, status_code=201)
async def create_area(
    request: AreaCreate,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    area = await area_service.create_area(db, request.model_dump())
    return AreaResponse(
        id=str(area["_id"]),
        **{k: v for k, v in area.items() if k != "_id"},
    )


@router.get("/", response_model=AreaListResponse)
async def get_areas(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    zone: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    result = await area_service.get_all_areas(db, page, limit, zone, district)
    areas = [
        AreaResponse(
            id=str(a["_id"]),
            **{k: v for k, v in a.items() if k != "_id"},
        )
        for a in result["areas"]
    ]
    return AreaListResponse(
        areas=areas,
        total=result["total"],
    )


@router.get("/zones")
async def get_zones(
    district: Optional[str] = Query(None),
    current_user=Depends(require_role(UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    zones = await area_service.get_zones(db, district)
    return {"zones": zones}


@router.get("/districts")
async def get_districts(
    current_user=Depends(require_role(UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    districts = await area_service.get_districts(db)
    return {"districts": districts}


@router.get("/resolve")
async def resolve_area(
    latitude: float = Query(...),
    longitude: float = Query(...),
    current_user=Depends(get_current_active_user),
    db=Depends(get_db),
):
    area_info = await complaint_service.resolve_area_from_coordinates(db, latitude, longitude)
    return area_info


@router.get("/{area_id}", response_model=AreaResponse)
async def get_area(
    area_id: str,
    current_user=Depends(require_role(UserRole.LOCAL_OFFICER, UserRole.ZONAL_OFFICER, UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    area = await area_service.get_area_by_id(db, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return AreaResponse(
        id=str(area["_id"]),
        **{k: v for k, v in area.items() if k != "_id"},
    )


@router.put("/{area_id}", response_model=AreaResponse)
async def update_area(
    area_id: str,
    request: AreaUpdate,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        area = await area_service.update_area(db, area_id, update_data)
        return AreaResponse(
            id=str(area["_id"]),
            **{k: v for k, v in area.items() if k != "_id"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{area_id}")
async def delete_area(
    area_id: str,
    current_user=Depends(require_role(UserRole.DISTRICT_OFFICER)),
    db=Depends(get_db),
):
    deleted = await area_service.delete_area(db, area_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Area not found")
    return {"message": "Area deactivated successfully"}