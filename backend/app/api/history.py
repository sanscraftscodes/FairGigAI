from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

from app.db.database import get_db
from app.db.models import AllocationRecordModel
from app.schemas.allocation import AllocationRecordResponse

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=dict)
def get_allocation_history(
    policy: Optional[str] = None,
    worker_id: Optional[str] = None,
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(AllocationRecordModel)

    if policy and policy != "all":
        query = query.filter(AllocationRecordModel.policy == policy)

    if status and status != "all":
        query = query.filter(AllocationRecordModel.status == status)

    if worker_id:
        query = query.filter(AllocationRecordModel.worker_id.ilike(f"%{worker_id}%"))

    if task_id:
        query = query.filter(AllocationRecordModel.task_id.ilike(f"%{task_id}%"))

    total = query.count()
    records = query.order_by(desc(AllocationRecordModel.timestamp)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "allocations": [AllocationRecordResponse.from_orm(r) for r in records]
    }

@router.get("/{allocation_id}")
def get_history_detail(allocation_id: str, db: Session = Depends(get_db)):
    record = db.query(AllocationRecordModel).filter(
        AllocationRecordModel.allocation_id == allocation_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Allocation {allocation_id} not found")

    rankings = []
    if record.candidate_rankings_json:
        try:
            rankings = json.loads(record.candidate_rankings_json)
        except Exception:
            pass

    return {
        "allocation": AllocationRecordResponse.from_orm(record),
        "rankings": rankings
    }
