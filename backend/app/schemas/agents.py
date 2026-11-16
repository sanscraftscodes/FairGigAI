from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class AgentStageResult(BaseModel):
    agent_id: str
    name: str
    role_description: str
    stage_number: int
    status: str  # Idle, Running, Completed, Failed
    duration_ms: float = 0.0
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

class WorkflowExecutionResponse(BaseModel):
    task_id: str
    stages: List[AgentStageResult]
    overall_status: str
    total_duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
