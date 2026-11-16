from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json
import uuid
from datetime import datetime

from app.db.database import get_db
from app.db.models import TaskModel, WorkerModel, AllocationRecordModel
from app.schemas.allocation import (
    AllocationPreviewRequest, AllocationRunRequest, AllocationResponse, AllocationRecordResponse, AllocationExplainRequest
)
from app.services.allocation_service import evaluate_candidates_for_task
from app.services.ai_service import explain_allocation

router = APIRouter(prefix="/allocation", tags=["Allocation"])

@router.post("/preview", response_model=dict)
def preview_allocation(payload: AllocationPreviewRequest, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    workers = db.query(WorkerModel).all()

    result = evaluate_candidates_for_task(
        task=task,
        workers=workers,
        lambda_val=payload.lambda_val,
        policy=payload.policy,
        max_candidates=payload.max_candidates
    )

    return result

@router.post("/run", response_model=dict)
def run_allocation(payload: AllocationRunRequest, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    workers = db.query(WorkerModel).all()

    result = evaluate_candidates_for_task(
        task=task,
        workers=workers,
        lambda_val=payload.lambda_val,
        policy=payload.policy,
        max_candidates=payload.max_candidates
    )

    if not result.get("selected_worker"):
        return result

    selected = result["selected_worker"]

    # If confirm flag is true, persist to database
    if payload.confirm:
        alloc_id = f"ALC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

        record = AllocationRecordModel(
            allocation_id=alloc_id,
            task_id=task.task_id,
            worker_id=selected["worker_id"],
            predicted_success=selected["predicted_success"],
            efficiency=selected["efficiency"],
            opportunity_credit=selected["opportunity_credit"],
            workload_pressure=selected["workload_pressure"],
            wafr_score=selected["wafr_score"],
            lambda_val=payload.lambda_val,
            policy=payload.policy,
            status="confirmed",
            explanation=result["detailed_explanation"],
            candidate_rankings_json=json.dumps(result["top_candidates"]),
            timestamp=datetime.utcnow()
        )
        db.add(record)

        # Update task status
        task.status = "allocated"
        task.allocated_worker_id = selected["worker_id"]
        task.allocation_id = alloc_id

        # Update worker task count and exposure
        worker = db.query(WorkerModel).filter(WorkerModel.worker_id == selected["worker_id"]).first()
        if worker:
            worker.total_tasks_allocated += 1
            worker.historical_tasks_7d += 1
            worker.working_hours_7d += round(task.estimated_duration_min / 60.0, 1)

        db.commit()
        result["allocation_id"] = alloc_id
        result["status"] = "confirmed"

    return result

@router.post("/explain", response_model=dict)
async def explain_allocation_endpoint(payload: AllocationExplainRequest, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    workers = db.query(WorkerModel).all()
    eval_result = evaluate_candidates_for_task(
        task=task,
        workers=workers,
        lambda_val=payload.lambda_val,
        policy=payload.policy,
        max_candidates=100
    )

    top_candidates = eval_result.get("top_candidates", [])

    # Locate winner
    selected_worker = None
    for cand in top_candidates:
        if cand.get("worker_id") == payload.worker_id:
            selected_worker = cand
            break
    if not selected_worker and eval_result.get("selected_worker"):
        selected_worker = eval_result["selected_worker"]

    if not selected_worker:
        raise HTTPException(status_code=400, detail="No eligible worker found to explain")

    # Locate runner-up
    runner_up = None
    if payload.runner_up_id:
        for cand in top_candidates:
            if cand.get("worker_id") == payload.runner_up_id:
                runner_up = cand
                break
    if not runner_up and len(top_candidates) > 1:
        for cand in top_candidates:
            if cand.get("worker_id") != selected_worker.get("worker_id") and cand.get("eligible"):
                runner_up = cand
                break

    task_dict = {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "priority": task.priority,
        "estimated_duration_min": task.estimated_duration_min,
        "package_weight_kg": task.package_weight_kg,
        "required_vehicle": getattr(task, "vehicle_required", "bike"),
        "base_payout": getattr(task, "payment", 25.0)
    }

    explanation_res = await explain_allocation(
        task=task_dict,
        selected_worker=selected_worker,
        runner_up=runner_up,
        policy=payload.policy,
        lambda_val=payload.lambda_val
    )

    return explanation_res

@router.get("/{allocation_id}")
def get_allocation_by_id(allocation_id: str, db: Session = Depends(get_db)):
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
