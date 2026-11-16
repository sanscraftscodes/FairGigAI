import json
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text
from app.config import DATA_DIR
from app.db.database import engine, SessionLocal, Base
from app.db.models import TaskModel, WorkerModel, AllocationRecordModel, AgentExecutionLogModel

def seed_database():
    print(f"Initializing database with {engine.dialect.name}.")
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(741852963)"))
        Base.metadata.create_all(bind=connection)

    db = SessionLocal()

    try:
        if engine.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(741852963)"))

        # Check if already seeded
        worker_count = db.query(WorkerModel).count()
        task_count = db.query(TaskModel).count()

        if worker_count == 0:
            workers_csv = DATA_DIR / "workers.csv"
            if workers_csv.exists():
                print(f"Loading workers from {workers_csv}...")
                df_workers = pd.read_csv(workers_csv)
                for _, row in df_workers.iterrows():
                    worker = WorkerModel(
                        worker_id=str(row["worker_id"]),
                        experience_years=float(row.get("experience_years", 2.0)),
                        current_lat=float(row.get("current_lat", 18.5204)),
                        current_lon=float(row.get("current_lon", 73.8567)),
                        availability_status=str(row.get("availability_status", "available")),
                        worker_status=str(row.get("worker_status", "active")),
                        vehicle_type=str(row.get("vehicle_type", "bike")),
                        vehicle_available=bool(row.get("vehicle_available", True)),
                        max_package_weight_kg=float(row.get("max_package_weight_kg", 15.0)),
                        archetype=str(row.get("archetype", "balanced")),
                        skills=str(row.get("skills", "driving,navigation")),
                        historical_tasks_7d=int(row.get("historical_tasks_7d", 12)),
                        historical_tasks_30d=int(row.get("historical_tasks_30d", 48)),
                        historical_tasks_90d=int(row.get("historical_tasks_90d", 130)),
                        success_rate_7d=float(row.get("success_rate_7d", 0.85)),
                        success_rate_30d=float(row.get("success_rate_30d", 0.85)),
                        success_rate_90d=float(row.get("success_rate_90d", 0.85)),
                        cancellation_rate_7d=float(row.get("cancellation_rate_7d", 0.05)),
                        cancellation_rate_30d=float(row.get("cancellation_rate_30d", 0.05)),
                        avg_delay_min_7d=float(row.get("avg_delay_min_7d", 6.0)),
                        avg_delay_min_30d=float(row.get("avg_delay_min_30d", 6.0)),
                        working_hours_7d=float(row.get("working_hours_7d", 22.0)),
                        working_hours_30d=float(row.get("working_hours_30d", 88.0)),
                        working_hours_90d=float(row.get("working_hours_90d", 240.0)),
                        success_delivery=float(row.get("success_delivery", 0.75)),
                        success_medicine=float(row.get("success_medicine", 0.75)),
                        success_food=float(row.get("success_food", 0.75)),
                        success_fragile=float(row.get("success_fragile", 0.75)),
                        success_document=float(row.get("success_document", 0.75)),
                        success_grocery=float(row.get("success_grocery", 0.75)),
                        workload_trend=float(row.get("workload_trend", 0.0)),
                        recent_exposure=float(row.get("recent_exposure", 0.25)),
                        total_tasks_allocated=0,
                        is_synthetic=False
                    )
                    db.add(worker)
                print(f"Successfully loaded {len(df_workers)} workers.")
            else:
                print(f"Workers CSV not found at {workers_csv}")
        else:
            print(f"Workers already seeded: {worker_count} records.")

        if task_count == 0:
            tasks_csv = DATA_DIR / "tasks.csv"
            if tasks_csv.exists():
                print(f"Loading tasks from {tasks_csv}...")
                df_tasks = pd.read_csv(tasks_csv)
                for _, row in df_tasks.iterrows():
                    task = TaskModel(
                        task_id=str(row["task_id"]),
                        task_type=str(row.get("task_type", "delivery")),
                        pickup_lat=float(row.get("pickup_lat", 18.5204)),
                        pickup_lon=float(row.get("pickup_lon", 73.8567)),
                        destination_lat=float(row.get("destination_lat", 18.5204)),
                        destination_lon=float(row.get("destination_lon", 73.8567)),
                        priority=str(row.get("priority", "medium")),
                        priority_num=int(row.get("priority_num", 1)),
                        estimated_duration_min=float(row.get("estimated_duration_min", 45.0)),
                        deadline_min=float(row.get("deadline_min", 120.0)),
                        payment=float(row.get("payment", 250.0)),
                        package_weight_kg=float(row.get("package_weight_kg", 5.0)),
                        vehicle_required=str(row.get("vehicle_required", "bike")),
                        required_skill=str(row.get("required_skill", "driving")),
                        status="unallocated",
                        allocated_worker_id=None,
                        allocation_id=None,
                        is_demo_seed=True
                    )
                    db.add(task)
                print(f"Successfully loaded {len(df_tasks)} tasks.")
            else:
                print(f"Tasks CSV not found at {tasks_csv}")
        else:
            print(f"Tasks already seeded: {task_count} records.")

        db.flush()

        # Seed initial allocations for historical demonstration if empty
        alloc_count = db.query(AllocationRecordModel).count()
        if alloc_count == 0:
            print("Seeding initial demonstration allocation history...")
            tasks_sample = db.query(TaskModel).limit(20).all()
            workers_sample = db.query(WorkerModel).filter(WorkerModel.availability_status == "available").limit(20).all()

            for i, task in enumerate(tasks_sample):
                if i >= len(workers_sample):
                    break
                worker = workers_sample[i]
                alloc_id = f"ALC-{datetime.utcnow().strftime('%Y%m%d')}-{i+1:04d}"
                pred_success = round(0.72 + (i % 5) * 0.045, 4)
                eff = round(0.68 + (i % 4) * 0.06, 4)
                opp = round(0.55 + (i % 6) * 0.05, 4)
                pressure = round(0.35 + (i % 3) * 0.1, 4)
                wafr = round(0.70 * pred_success + 0.30 * eff + 0.08 * opp - 0.08 * pressure, 4)

                policy = "WAFR" if i % 4 != 0 else ("ML-Only" if i % 2 == 0 else "Nearest Eligible")
                created_time = datetime.utcnow() - timedelta(hours=i * 2 + 1)

                record = AllocationRecordModel(
                    allocation_id=alloc_id,
                    task_id=task.task_id,
                    worker_id=worker.worker_id,
                    predicted_success=pred_success,
                    efficiency=eff,
                    opportunity_credit=opp,
                    workload_pressure=pressure,
                    wafr_score=wafr,
                    lambda_val=0.08,
                    policy=policy,
                    status="confirmed",
                    explanation=f"Worker {worker.worker_id} chosen via {policy}. High compatibility with {task.task_type} tasks and balanced workload.",
                    candidate_rankings_json=json.dumps([
                        {"rank": 1, "worker_id": worker.worker_id, "wafr_score": wafr, "predicted_success": pred_success, "eligible": True},
                        {"rank": 2, "worker_id": "W0482", "wafr_score": round(wafr - 0.03, 4), "predicted_success": round(pred_success - 0.02, 4), "eligible": True}
                    ]),
                    timestamp=created_time
                )
                db.add(record)

                # Update task and worker stats
                task.status = "allocated"
                task.allocated_worker_id = worker.worker_id
                task.allocation_id = alloc_id
                worker.total_tasks_allocated += 1

            print("Successfully seeded demonstration allocation history.")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error during database seed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
