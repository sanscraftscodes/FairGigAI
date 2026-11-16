from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np

from app.db.database import get_db
from app.db.models import TaskModel, WorkerModel, AllocationRecordModel
from app.services.fairness_service import calculate_jain_index, calculate_gini_index
from app.services.allocation_service import simulate_policy_comparison

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_workers = db.query(WorkerModel).count()
    total_tasks = db.query(TaskModel).count()
    available_workers = db.query(WorkerModel).filter(WorkerModel.availability_status == "available").count()
    tasks_allocated = db.query(AllocationRecordModel).filter(AllocationRecordModel.status == "confirmed").count()

    allocations = db.query(AllocationRecordModel).filter(AllocationRecordModel.status == "confirmed").all()

    if allocations:
        avg_pred_success = float(np.mean([a.predicted_success for a in allocations]))
        worker_ids = [a.worker_id for a in allocations]
        exp_series = pd.Series(worker_ids).value_counts()
        jain_fairness = calculate_jain_index(exp_series)
        gini_exposure = calculate_gini_index(exp_series)
    else:
        avg_pred_success = 0.0
        jain_fairness = 0.0
        gini_exposure = 0.0

    # Chart A: Allocation Distribution by Task Type
    task_types_q = (
        db.query(TaskModel.task_type, func.count(AllocationRecordModel.allocation_id))
        .join(AllocationRecordModel, TaskModel.task_id == AllocationRecordModel.task_id)
        .group_by(TaskModel.task_type)
        .all()
    )
    alloc_distribution = [
        {"name": tt, "value": count} for tt, count in task_types_q if count > 0
    ]
    if not alloc_distribution:
        # Fallback to general task types if no allocations yet
        types_q = db.query(TaskModel.task_type, func.count(TaskModel.task_id)).group_by(TaskModel.task_type).all()
        alloc_distribution = [{"name": tt, "value": count} for tt, count in types_q]

    # Chart B: Worker Workload Distribution (sample of workers)
    workers_sample = db.query(WorkerModel).order_by(WorkerModel.total_tasks_allocated.desc()).limit(10).all()
    workload_chart = [
        {
            "worker_id": w.worker_id,
            "working_hours_7d": round(w.working_hours_7d, 1),
            "allocated_tasks": w.total_tasks_allocated,
            "vehicle_type": w.vehicle_type
        }
        for w in workers_sample
    ]

    # Chart C: Recent Allocation Activity
    recent_allocs = (
        db.query(AllocationRecordModel)
        .order_by(AllocationRecordModel.timestamp.desc())
        .limit(6)
        .all()
    )
    recent_activity = [
        {
            "allocation_id": a.allocation_id,
            "task_id": a.task_id,
            "worker_id": a.worker_id,
            "predicted_success": a.predicted_success,
            "policy": a.policy,
            "wafr_score": a.wafr_score,
            "timestamp": a.timestamp.isoformat(),
            "status": a.status
        }
        for a in recent_allocs
    ]

    # Quick policy comparison metrics
    tasks_for_sim = db.query(TaskModel).filter(TaskModel.status == "unallocated").limit(15).all()
    if not tasks_for_sim:
        tasks_for_sim = db.query(TaskModel).limit(15).all()
    workers_for_sim = db.query(WorkerModel).filter(WorkerModel.availability_status == "available").limit(50).all()

    policy_comp = simulate_policy_comparison(tasks_for_sim, workers_for_sim, lambda_val=0.08)

    return {
        "kpis": {
            "total_workers": total_workers,
            "total_tasks": total_tasks,
            "available_workers": available_workers,
            "tasks_allocated": tasks_allocated,
            "avg_predicted_success": round(avg_pred_success, 4),
            "jain_fairness": round(jain_fairness, 4),
            "gini_exposure": round(gini_exposure, 4)
        },
        "charts": {
            "allocation_distribution": alloc_distribution,
            "worker_workload": workload_chart,
            "policy_comparison": policy_comp,
            "recent_activity": recent_activity
        }
    }
