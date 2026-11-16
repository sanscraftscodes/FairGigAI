from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from typing import Optional, List
import uuid
from datetime import datetime

from app.db.database import get_db
from app.db.models import WorkerModel, AllocationRecordModel
from app.schemas.worker import WorkerCreate, WorkerResponse

router = APIRouter(prefix="/workers", tags=["Workers"])

@router.get("", response_model=dict)
def get_workers(
    skill: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    availability: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "worker_id",
    sort_order: Optional[str] = "asc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(WorkerModel)

    if vehicle_type and vehicle_type != "all":
        query = query.filter(WorkerModel.vehicle_type == vehicle_type)

    if availability and availability != "all":
        query = query.filter(WorkerModel.availability_status == availability)

    if skill and skill != "all":
        query = query.filter(WorkerModel.skills.ilike(f"%{skill}%"))

    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                WorkerModel.worker_id.ilike(s),
                WorkerModel.archetype.ilike(s),
                WorkerModel.skills.ilike(s)
            )
        )

    # Sorting
    sort_column = getattr(WorkerModel, sort_by, WorkerModel.worker_id)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    total = query.count()
    workers = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "workers": [WorkerResponse.from_orm(w) for w in workers]
    }

@router.get("/{worker_id}")
def get_worker_detail(worker_id: str, db: Session = Depends(get_db)):
    worker = db.query(WorkerModel).filter(WorkerModel.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")

    allocations = (
        db.query(AllocationRecordModel)
        .filter(AllocationRecordModel.worker_id == worker_id)
        .order_by(AllocationRecordModel.timestamp.desc())
        .limit(10)
        .all()
    )

    return {
        "worker": WorkerResponse.from_orm(worker),
        "recent_allocations": allocations,
        "performance_profile": {
            "success_rate_30d": worker.success_rate_30d,
            "cancellation_rate_30d": worker.cancellation_rate_30d,
            "avg_delay_min_30d": worker.avg_delay_min_30d,
            "working_hours_7d": worker.working_hours_7d,
            "working_hours_30d": worker.working_hours_30d,
            "recent_exposure": worker.recent_exposure,
            "workload_trend": worker.workload_trend,
            "affinities": {
                "delivery": worker.success_delivery,
                "medicine": worker.success_medicine,
                "food": worker.success_food,
                "fragile": worker.success_fragile,
                "document": worker.success_document,
                "grocery": worker.success_grocery
            }
        }
    }

@router.post("/synthetic", response_model=WorkerResponse)
def create_synthetic_worker(payload: WorkerCreate, db: Session = Depends(get_db)):
    """Creates a clearly labeled synthetic demo worker."""
    worker_id = payload.worker_id or f"W-SYN-{uuid.uuid4().hex[:4].upper()}"

    existing = db.query(WorkerModel).filter(WorkerModel.worker_id == worker_id).first()
    if existing:
        worker_id = f"W-SYN-{uuid.uuid4().hex[:6].upper()}"

    worker = WorkerModel(
        worker_id=worker_id,
        experience_years=payload.experience_years,
        current_lat=payload.current_lat,
        current_lon=payload.current_lon,
        availability_status=payload.availability_status,
        worker_status="active",
        vehicle_type=payload.vehicle_type,
        vehicle_available=payload.vehicle_available,
        max_package_weight_kg=payload.max_package_weight_kg,
        archetype=payload.archetype,
        skills=payload.skills,
        historical_tasks_7d=10,
        historical_tasks_30d=40,
        historical_tasks_90d=110,
        success_rate_7d=0.82,
        success_rate_30d=0.84,
        success_rate_90d=0.85,
        cancellation_rate_7d=0.04,
        cancellation_rate_30d=0.04,
        avg_delay_min_7d=5.0,
        avg_delay_min_30d=5.0,
        working_hours_7d=18.0,
        working_hours_30d=72.0,
        working_hours_90d=210.0,
        success_delivery=0.80,
        success_medicine=0.75,
        success_food=0.82,
        success_fragile=0.70,
        success_document=0.85,
        success_grocery=0.78,
        workload_trend=0.0,
        recent_exposure=0.25,
        total_tasks_allocated=0,
        is_synthetic=True,
        created_at=datetime.utcnow()
    )

    db.add(worker)
    db.commit()
    db.refresh(worker)
    return WorkerResponse.from_orm(worker)
