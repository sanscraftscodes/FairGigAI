from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import TaskModel, WorkerModel
from app.agents.task_analysis import TaskAnalysisAgent
from app.agents.worker_suitability import WorkerSuitabilityAgent
from app.agents.fairness_evaluation import FairnessEvaluationAgent
from app.agents.allocation_agent import AllocationAgent
from app.agents.explainability import ExplainabilityAgent
from app.services.model_service import model_service
from app.services.feature_builder import build_feature_rows

router = APIRouter(prefix="/agents", tags=["Agents"])

class AgentRunRequest(BaseModel):
    task_id: str
    lambda_val: float = 0.08
    policy: str = "WAFR"
    max_candidates: int = 50

@router.get("/status")
def get_agents_status():
    """Returns metadata and current operational state of all pipeline components."""
    return {
        "pipeline": [
            {
                "agent_id": "agent_task_analysis",
                "name": "Agent 1: Task Analysis Agent",
                "type": "Agent",
                "role": "Task Analysis & Validation",
                "purpose": "Interprets task attributes, extracts constraints, assesses completeness and data quality.",
                "status": "Idle",
                "input_spec": "Raw Task Attributes (type, location, deadline, weight, priority, skills)",
                "output_spec": "Structured Task Object, validation report, and quality score"
            },
            {
                "agent_id": "agent_worker_suitability",
                "name": "Agent 2: Worker Profile & Suitability Agent",
                "type": "Agent",
                "role": "Compatibility & Eligibility Filtering",
                "purpose": "Verifies mandatory constraints (vehicle, skills, package capacity, availability, travel deadline).",
                "status": "Idle",
                "input_spec": "Structured Task Object + Worker Directory Profiles",
                "output_spec": "Eligible & Ineligible worker candidate pools with explicit rejection justifications"
            },
            {
                "agent_id": "service_ml_prediction",
                "name": "Component 3: ML Success Prediction Service",
                "type": "ML Service (Trained Ensemble)",
                "role": "Task Success Likelihood Estimation",
                "purpose": "Applies dual-model ensemble (HistGradientBoosting 0.5 + CatBoost 0.5) to compute task success probability.",
                "status": "Operational" if model_service.is_loaded else "Degraded",
                "input_spec": "27 candidate features (25 numerical, 2 categorical)",
                "output_spec": "Predicted success probability P_succ for each eligible worker"
            },
            {
                "agent_id": "agent_fairness_evaluation",
                "name": "Agent 4: Fairness Evaluation Agent",
                "type": "Agent",
                "role": "Workload & Opportunity Assessment",
                "purpose": "Analyzes recent task exposure, historical working hours, and computes opportunity credit and workload pressure.",
                "status": "Idle",
                "input_spec": "Worker 7d/30d workload history + exposure metrics",
                "output_spec": "Operational efficiency, opportunity credit, and workload pressure signals"
            },
            {
                "agent_id": "agent_allocation",
                "name": "Agent 5: Allocation Agent",
                "type": "Agent",
                "role": "WAFR Multi-Objective Optimization",
                "purpose": "Combines ML prediction, operational efficiency, and fairness terms to rank candidates and select the winner.",
                "status": "Idle",
                "input_spec": "ML predictions + Efficiency + Fairness signals + Configured λ parameter",
                "output_spec": "Final WAFR score rankings and chosen worker assignment"
            },
            {
                "agent_id": "agent_explainability",
                "name": "Agent 6: Explainability Agent",
                "type": "Agent",
                "role": "Transparent Decision Explanation",
                "purpose": "Generates data-grounded justifications, score decompositions, and counterfactual comparisons against alternative candidates.",
                "status": "Idle",
                "input_spec": "Allocation decision, candidate scores, and worker profiles",
                "output_spec": "Human-readable explanation, mathematical decomposition, and runner-up delta"
            }
        ]
    }

@router.post("/run")
def run_agents_workflow(payload: AgentRunRequest, db: Session = Depends(get_db)):
    """Executes the live end-to-end multi-agent pipeline."""
    task = db.query(TaskModel).filter(TaskModel.task_id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    workers = db.query(WorkerModel).all()
    overall_start = time.time()
    stages = []

    # 1. Task Analysis Agent
    ta_agent = TaskAnalysisAgent()
    stage1_res = ta_agent.run(task)
    stages.append(stage1_res)

    # 2. Worker Suitability Agent
    ws_agent = WorkerSuitabilityAgent()
    stage2_res = ws_agent.run(task, workers, max_candidates=payload.max_candidates)
    stages.append({
        "agent_id": stage2_res["agent_id"],
        "name": stage2_res["name"],
        "role_description": stage2_res["role_description"],
        "stage_number": stage2_res["stage_number"],
        "status": stage2_res["status"],
        "duration_ms": stage2_res["duration_ms"],
        "input_summary": stage2_res["input_summary"],
        "output_summary": stage2_res["output_summary"]
    })

    eligible_candidates = stage2_res["eligible_candidates"]

    # 3. Component 3: ML Success Prediction Service
    ml_start = time.time()
    if eligible_candidates:
        feature_rows = [c["features"] for c in eligible_candidates]
        ordered_feature_rows = build_feature_rows(feature_rows)
        ens_probs, hgb_probs, cat_probs = model_service.predict_probabilities(
            ordered_feature_rows
        )

        for i, c in enumerate(eligible_candidates):
            c["predicted_success"] = round(float(ens_probs[i]), 4)
            c["hgb_prob"] = round(float(hgb_probs[i]), 4)
            c["cat_prob"] = round(float(cat_probs[i]), 4)

        ml_duration = (time.time() - ml_start) * 1000
        stages.append({
            "agent_id": "service_ml_prediction",
            "name": "Component 3: ML Success Prediction Service",
            "role_description": "Applies trained ensemble (HistGradientBoosting 0.5 + CatBoost 0.5) to predict success probabilities.",
            "stage_number": 3,
            "status": "Completed",
            "duration_ms": round(ml_duration, 2),
            "input_summary": {
                "eligible_candidates_evaluated": len(eligible_candidates),
                "feature_count": 27
            },
            "output_summary": {
                "mean_predicted_success": round(float(ens_probs.mean()), 4),
                "max_predicted_success": round(float(ens_probs.max()), 4),
                "min_predicted_success": round(float(ens_probs.min()), 4)
            }
        })
    else:
        stages.append({
            "agent_id": "service_ml_prediction",
            "name": "Component 3: ML Success Prediction Service",
            "role_description": "Applies trained ensemble to predict success probabilities.",
            "stage_number": 3,
            "status": "Skipped",
            "duration_ms": 0.0,
            "input_summary": {"eligible_candidates": 0},
            "output_summary": {"message": "No eligible candidates passed suitability filtering."}
        })

    # 4. Fairness Evaluation Agent
    fe_agent = FairnessEvaluationAgent()
    stage4_res = fe_agent.run(eligible_candidates, lambda_val=payload.lambda_val)
    stages.append(stage4_res)

    # 5. Allocation Agent
    alloc_agent = AllocationAgent()
    stage5_res = alloc_agent.run(eligible_candidates, lambda_val=payload.lambda_val, policy=payload.policy)
    stages.append({
        "agent_id": stage5_res["agent_id"],
        "name": stage5_res["name"],
        "role_description": stage5_res["role_description"],
        "stage_number": stage5_res["stage_number"],
        "status": stage5_res["status"],
        "duration_ms": stage5_res["duration_ms"],
        "input_summary": stage5_res["input_summary"],
        "output_summary": stage5_res["output_summary"]
    })

    selected_worker = stage5_res["selected_worker"]
    ranked_candidates = stage5_res["ranked_candidates"]

    # 6. Explainability Agent
    exp_agent = ExplainabilityAgent()
    stage6_res = exp_agent.run(
        task=task,
        selected_worker=selected_worker,
        ranked_candidates=ranked_candidates,
        policy=payload.policy,
        lambda_val=payload.lambda_val
    )
    stages.append(stage6_res)

    total_duration_ms = (time.time() - overall_start) * 1000

    return {
        "task_id": str(task.task_id),
        "stages": stages,
        "selected_worker": selected_worker,
        "overall_status": "Success" if selected_worker else "No Assignment",
        "total_duration_ms": round(total_duration_ms, 2)
    }
