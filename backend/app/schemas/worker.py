from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class WorkerBase(BaseModel):
    experience_years: float = Field(default=2.0)
    current_lat: float = Field(default=18.5204)
    current_lon: float = Field(default=73.8567)
    availability_status: str = Field(default="available")
    worker_status: str = Field(default="active")
    vehicle_type: str = Field(default="bike")
    vehicle_available: bool = Field(default=True)
    max_package_weight_kg: float = Field(default=15.0)
    archetype: str = Field(default="balanced")
    skills: str = Field(default="driving,navigation")

class WorkerCreate(WorkerBase):
    worker_id: Optional[str] = None

class WorkerResponse(WorkerBase):
    worker_id: str
    historical_tasks_7d: int
    historical_tasks_30d: int
    historical_tasks_90d: int
    success_rate_7d: float
    success_rate_30d: float
    success_rate_90d: float
    cancellation_rate_7d: float
    cancellation_rate_30d: float
    avg_delay_min_7d: float
    avg_delay_min_30d: float
    working_hours_7d: float
    working_hours_30d: float
    working_hours_90d: float
    success_delivery: float
    success_medicine: float
    success_food: float
    success_fragile: float
    success_document: float
    success_grocery: float
    workload_trend: float
    recent_exposure: float
    total_tasks_allocated: int
    is_synthetic: bool
    created_at: datetime

    class Config:
        from_attributes = True
