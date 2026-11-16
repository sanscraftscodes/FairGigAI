from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FairnessSummaryResponse(BaseModel):
    jain_exposure: float
    gini_exposure: float
    worker_coverage: float
    zero_exposure_rate: float
    allocated_tasks: int
    average_workload_hours: float
    total_workers: int
    distribution_exposure: List[Dict[str, Any]] = Field(default_factory=list)
    workload_distribution: List[Dict[str, Any]] = Field(default_factory=list)

class PolicyComparisonMetric(BaseModel):
    policy: str
    lambda_val: Optional[float] = None
    tasks_allocated: int
    mean_distance_km: float
    mean_predicted_success: float
    jain_exposure: float
    gini_exposure: float
    worker_coverage: float
    zero_exposure_rate: float
    efficiency_avg: float

class LambdaSweepPoint(BaseModel):
    lambda_val: float
    jain_exposure: float
    gini_exposure: float
    worker_coverage: float
    mean_predicted_success: float
    mean_distance_km: float

class LambdaSweepResponse(BaseModel):
    sweep_results: List[LambdaSweepPoint]
    interpretation: str
