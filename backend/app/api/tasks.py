from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
import uuid
from datetime import datetime

from app.db.database import get_db
from app.db.models import TaskModel, AllocationRecordModel
from app.schemas.task import TaskCreate, TaskResponse
from app.services.feature_builder import PRIORITY_MAP

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=dict)
def get_tasks(
    task_type: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(TaskModel)

    if task_type and task_type != "all":
        query = query.filter(TaskModel.task_type == task_type)

    if priority and priority != "all":
        query = query.filter(TaskModel.priority == priority)

    if status and status != "all":
        query = query.filter(TaskModel.status == status)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                TaskModel.task_id.ilike(search_filter),
                TaskModel.task_type.ilike(search_filter),
                TaskModel.required_skill.ilike(search_filter)
            )
        )

    total = query.count()
    tasks = query.order_by(TaskModel.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "tasks": [TaskResponse.from_orm(t) for t in tasks]
    }

@router.get("/{task_id}")
def get_task_detail(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    allocation = None
    if task.allocation_id:
        allocation = db.query(AllocationRecordModel).filter(
            AllocationRecordModel.allocation_id == task.allocation_id
        ).first()

    return {
        "task": TaskResponse.from_orm(task),
        "allocation": allocation
    }

@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task_id = payload.task_id or f"T{uuid.uuid4().hex[:6].upper()}"

    # Verify ID uniqueness
    existing = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if existing:
        task_id = f"T{uuid.uuid4().hex[:8].upper()}"

    priority_num = PRIORITY_MAP.get(payload.priority.lower(), 1)

    new_task = TaskModel(
        task_id=task_id,
        task_type=payload.task_type.lower(),
        pickup_lat=payload.pickup_lat,
        pickup_lon=payload.pickup_lon,
        destination_lat=payload.destination_lat,
        destination_lon=payload.destination_lon,
        priority=payload.priority.lower(),
        priority_num=priority_num,
        estimated_duration_min=payload.estimated_duration_min,
        deadline_min=payload.deadline_min,
        payment=payload.payment,
        package_weight_kg=payload.package_weight_kg,
        vehicle_required=payload.vehicle_required.lower(),
        required_skill=payload.required_skill.lower(),
        status="unallocated",
        is_demo_seed=False,
        created_at=datetime.utcnow()
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return TaskResponse.from_orm(new_task)

@router.post("/validate")
def validate_task_data(payload: TaskCreate):
    errors = []
    warnings = []

    if payload.estimated_duration_min >= payload.deadline_min:
        errors.append("Estimated duration cannot exceed deadline.")

    if payload.payment <= 0:
        errors.append("Payment must be greater than zero.")

    if payload.package_weight_kg > 40 and payload.vehicle_required in ["bike", "scooter"]:
        warnings.append(f"Heavy package ({payload.package_weight_kg}kg) may exceed two-wheeler safe transport capacity.")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "quality_score": 100 - len(errors) * 40 - len(warnings) * 15
    }
