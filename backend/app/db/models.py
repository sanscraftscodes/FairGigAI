from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from app.db.database import Base

class TaskModel(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    task_type = Column(String, index=True)
    pickup_lat = Column(Float)
    pickup_lon = Column(Float)
    destination_lat = Column(Float)
    destination_lon = Column(Float)
    priority = Column(String, index=True)
    priority_num = Column(Integer)
    estimated_duration_min = Column(Float)
    deadline_min = Column(Float)
    payment = Column(Float)
    package_weight_kg = Column(Float)
    vehicle_required = Column(String)
    required_skill = Column(String)
    status = Column(String, default="unallocated", index=True)  # unallocated, allocated, completed, cancelled
    allocated_worker_id = Column(String, nullable=True)
    allocation_id = Column(String, nullable=True)
    is_demo_seed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkerModel(Base):
    __tablename__ = "workers"

    worker_id = Column(String, primary_key=True, index=True)
    experience_years = Column(Float)
    current_lat = Column(Float)
    current_lon = Column(Float)
    availability_status = Column(String, index=True)  # available, busy, offline
    worker_status = Column(String, default="active")  # active, inactive
    vehicle_type = Column(String, index=True)         # bike, scooter, car, van
    vehicle_available = Column(Boolean, default=True)
    max_package_weight_kg = Column(Float)
    archetype = Column(String)
    skills = Column(String)                           # comma-separated

    # Historical metrics
    historical_tasks_7d = Column(Integer, default=10)
    historical_tasks_30d = Column(Integer, default=40)
    historical_tasks_90d = Column(Integer, default=120)
    success_rate_7d = Column(Float, default=0.85)
    success_rate_30d = Column(Float, default=0.85)
    success_rate_90d = Column(Float, default=0.85)
    cancellation_rate_7d = Column(Float, default=0.05)
    cancellation_rate_30d = Column(Float, default=0.05)
    avg_delay_min_7d = Column(Float, default=5.0)
    avg_delay_min_30d = Column(Float, default=5.0)
    working_hours_7d = Column(Float, default=20.0)
    working_hours_30d = Column(Float, default=80.0)
    working_hours_90d = Column(Float, default=240.0)

    # Task affinities
    success_delivery = Column(Float, default=0.75)
    success_medicine = Column(Float, default=0.75)
    success_food = Column(Float, default=0.75)
    success_fragile = Column(Float, default=0.75)
    success_document = Column(Float, default=0.75)
    success_grocery = Column(Float, default=0.75)

    workload_trend = Column(Float, default=0.0)
    recent_exposure = Column(Float, default=0.25)
    total_tasks_allocated = Column(Integer, default=0)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AllocationRecordModel(Base):
    __tablename__ = "allocations"

    allocation_id = Column(String, primary_key=True, index=True)
    task_id = Column(String, index=True)
    worker_id = Column(String, index=True)
    predicted_success = Column(Float)
    efficiency = Column(Float)
    opportunity_credit = Column(Float)
    workload_pressure = Column(Float)
    wafr_score = Column(Float)
    lambda_val = Column(Float)
    policy = Column(String, default="WAFR")  # WAFR, Nearest Eligible, ML-Only
    status = Column(String, default="confirmed")  # confirmed, draft, cancelled
    explanation = Column(Text)
    candidate_rankings_json = Column(Text)  # JSON string of top candidate evaluations
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class AgentExecutionLogModel(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allocation_id = Column(String, index=True)
    agent_name = Column(String)
    stage_number = Column(Integer)
    status = Column(String)  # Idle, Running, Completed, Failed
    duration_ms = Column(Float)
    input_summary = Column(Text)
    output_summary = Column(Text)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
