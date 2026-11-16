import io
import csv
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AllocationRecordModel, WorkerModel, TaskModel

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/allocation.csv")
def export_allocations_csv(db: Session = Depends(get_db)):
    allocations = db.query(AllocationRecordModel).order_by(AllocationRecordModel.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Allocation ID", "Task ID", "Worker ID", "Policy", "Predicted Success",
        "Efficiency", "Opportunity Credit", "Workload Pressure", "WAFR Score",
        "Lambda", "Status", "Timestamp"
    ])

    for a in allocations:
        writer.writerow([
            a.allocation_id, a.task_id, a.worker_id, a.policy, a.predicted_success,
            a.efficiency, a.opportunity_credit, a.workload_pressure, a.wafr_score,
            a.lambda_val, a.status, a.timestamp.isoformat()
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fairgig_allocations.csv"}
    )

@router.get("/workers.csv")
def export_workers_csv(db: Session = Depends(get_db)):
    workers = db.query(WorkerModel).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Worker ID", "Vehicle Type", "Skills", "Availability", "Experience Years",
        "7d Tasks", "30d Tasks", "7d Work Hours", "30d Work Hours", "Success Rate 30d",
        "Recent Exposure", "Total Allocated Tasks"
    ])

    for w in workers:
        writer.writerow([
            w.worker_id, w.vehicle_type, w.skills, w.availability_status, w.experience_years,
            w.historical_tasks_7d, w.historical_tasks_30d, w.working_hours_7d, w.working_hours_30d,
            w.success_rate_30d, w.recent_exposure, w.total_tasks_allocated
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fairgig_workers.csv"}
    )
