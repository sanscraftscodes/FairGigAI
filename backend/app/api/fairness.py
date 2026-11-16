from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from collections import Counter
import numpy as np

from app.db.database import get_db
from app.db.models import AllocationRecordModel, WorkerModel, TaskModel
from app.services.fairness_service import calculate_jain_index, calculate_gini_index
from app.services.allocation_service import simulate_policy_comparison, run_lambda_sweep

router = APIRouter(prefix="/fairness", tags=["Fairness"])

@router.get("/summary")
def get_fairness_summary(db: Session = Depends(get_db)):
    allocations = db.query(AllocationRecordModel).filter(AllocationRecordModel.status == "confirmed").all()
    workers = db.query(WorkerModel).all()
    total_workers = len(workers)

    if allocations:
        worker_ids = [a.worker_id for a in allocations]
        exposure_counts = Counter(worker_ids)
        jain = calculate_jain_index(list(exposure_counts.values()))
        gini = calculate_gini_index(list(exposure_counts.values()))
        coverage = len(exposure_counts) / max(1, total_workers)
        zero_exposure = 1.0 - coverage
        avg_workload = float(np.mean([w.working_hours_7d for w in workers]))

        # Top exposed workers
        dist_exposure = [
            {"worker_id": worker_id, "tasks_allocated": count}
            for worker_id, count in exposure_counts.most_common(10)
        ]
    else:
        jain = 0.0
        gini = 0.0
        coverage = 0.0
        zero_exposure = 1.0
        avg_workload = float(np.mean([w.working_hours_7d for w in workers])) if workers else 0.0
        dist_exposure = []

    # Workload distribution histogram bins (0-10h, 10-20h, 20-30h, 30-40h, 40h+)
    hours = [w.working_hours_7d for w in workers]
    bins = [0, 10, 20, 30, 40, 100]
    labels = ["0-10h", "10-20h", "20-30h", "30-40h", "40h+"]
    hist, _ = np.histogram(hours, bins=bins)
    workload_distribution = [
        {"range": label, "count": int(count)}
        for label, count in zip(labels, hist)
    ]

    return {
        "jain_exposure": round(jain, 4),
        "gini_exposure": round(gini, 4),
        "worker_coverage": round(coverage, 4),
        "zero_exposure_rate": round(zero_exposure, 4),
        "allocated_tasks": len(allocations),
        "average_workload_hours": round(avg_workload, 1),
        "total_workers": total_workers,
        "distribution_exposure": dist_exposure,
        "workload_distribution": workload_distribution
    }

@router.get("/policy-comparison")
def get_policy_comparison(lambda_val: float = Query(default=0.08, ge=0.0, le=1.0), db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).limit(20).all()
    workers = db.query(WorkerModel).filter(WorkerModel.availability_status == "available").limit(50).all()

    comparison = simulate_policy_comparison(tasks, workers, lambda_val=lambda_val)
    return {
        "policies": comparison,
        "lambda_used": lambda_val,
        "tasks_evaluated": len(tasks),
        "workers_considered": len(workers)
    }

@router.post("/sweep")
def get_lambda_sweep(db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).limit(15).all()
    workers = db.query(WorkerModel).filter(WorkerModel.availability_status == "available").limit(40).all()

    sweep_results = run_lambda_sweep(tasks, workers)

    interpretation = (
        "As λ increases from 0.0 to 0.50, the fairness weight prioritizes workers with lower recent exposure "
        "and penalizes high workload pressure. Notice that while Jain's fairness index generally improves with "
        "modest λ, excessive values may slightly increase average travel distance or alter predicted success. "
        "λ = 0.08 represents a balanced setting preserving high operational efficiency while preventing opportunity starvation."
    )

    return {
        "sweep_results": sweep_results,
        "interpretation": interpretation
    }
