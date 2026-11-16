from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class TaskBase(BaseModel):
    task_type: str = Field(..., description="Task type: delivery, medicine, food, fragile, document, grocery")
    pickup_lat: float = Field(default=18.5204)
    pickup_lon: float = Field(default=73.8567)
    destination_lat: float = Field(default=18.5204)
    destination_lon: float = Field(default=73.8567)
    priority: str = Field(default="medium", description="low, medium, high, urgent")
    estimated_duration_min: float = Field(..., ge=5, le=300)
    deadline_min: float = Field(..., ge=15, le=600)
    payment: float = Field(..., ge=10)
    package_weight_kg: float = Field(..., ge=0.1, le=100)
    vehicle_required: str = Field(default="none", description="bike, scooter, car, van, none")
    required_skill: str = Field(..., description="Required worker skill")

class TaskCreate(TaskBase):
    task_id: Optional[str] = None
    description: Optional[str] = None
    mandatory_requirements: Optional[List[str]] = None
    preferred_requirements: Optional[List[str]] = None
    special_handling: Optional[str] = None

class TaskResponse(TaskBase):
    task_id: str
    priority_num: int
    status: str
    allocated_worker_id: Optional[str] = None
    allocation_id: Optional[str] = None
    is_demo_seed: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
