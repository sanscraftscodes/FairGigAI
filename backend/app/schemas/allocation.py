from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class CandidateEvaluation(BaseModel):
    worker_id: str
    rank: int
    eligible: bool
    ineligibility_reasons: List[str] = Field(default_factory=list)
    distance_km: float
    predicted_success: Optional[float] = None
    efficiency: Optional[float] = None
    opportunity_credit: Optional[float] = None
    workload_pressure: Optional[float] = None
    wafr_score: Optional[float] = None
    hgb_prob: Optional[float] = None
    cat_prob: Optional[float] = None
    experience_years: float
    current_workload_hours: float
    vehicle_type: str
    availability_status: str

class AllocationPreviewRequest(BaseModel):
    task_id: str
    lambda_val: float = Field(default=0.08, ge=0.0, le=1.0)
    policy: str = Field(default="WAFR", description="WAFR, Nearest Eligible, ML-Only")
    max_candidates: int = Field(default=100, ge=10, le=1000)

class AllocationRunRequest(BaseModel):
    task_id: str
    lambda_val: float = Field(default=0.08, ge=0.0, le=1.0)
    policy: str = Field(default="WAFR")
    max_candidates: int = Field(default=100, ge=10, le=1000)
    selected_worker_id: Optional[str] = None
    confirm: bool = Field(default=False)

class AllocationResponse(BaseModel):
    allocation_id: Optional[str] = None
    task_id: str
    policy: str
    lambda_val: float
    total_candidates_examined: int
    eligible_count: int
    ineligible_count: int
    selected_worker: Optional[CandidateEvaluation] = None
    top_candidates: List[CandidateEvaluation] = Field(default_factory=list)
    decision_summary: str
    detailed_explanation: str
    status: str  # preview, confirmed, no_eligible_workers
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AllocationRecordResponse(BaseModel):
    allocation_id: str
    task_id: str
    worker_id: str
    predicted_success: float
    efficiency: float
    opportunity_credit: float
    workload_pressure: float
    wafr_score: float
    lambda_val: float
    policy: str
    status: str
    explanation: str
    candidate_rankings_json: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AllocationExplainRequest(BaseModel):
    task_id: str
    worker_id: str
    runner_up_id: Optional[str] = None
    policy: str = Field(default="WAFR")
    lambda_val: float = Field(default=0.08, ge=0.0, le=1.0)
