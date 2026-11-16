import time
import numpy as np
from typing import Dict, Any, List
from app.services.fairness_service import (
    compute_efficiency, compute_opportunity_credit, compute_workload_pressure
)

class FairnessEvaluationAgent:
    name = "Fairness Evaluation Agent"
    agent_id = "agent_fairness_evaluation"
    role_description = "Evaluates worker exposure distribution, recent workload pressure, opportunity credit, and fairness signals."
    stage_number = 4

    def run(self, eligible_candidates: List[Dict[str, Any]], lambda_val: float = 0.08) -> Dict[str, Any]:
        start_time = time.time()

        if not eligible_candidates:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role_description": self.role_description,
                "stage_number": self.stage_number,
                "status": "Completed",
                "duration_ms": 0.0,
                "input_summary": {"eligible_candidates_count": 0},
                "output_summary": {"message": "No eligible candidates to evaluate for fairness."}
            }

        distances = np.array([c["distance_km"] for c in eligible_candidates])
        pressures = np.array([c["features"]["deadline_pressure"] for c in eligible_candidates])
        exposures = np.array([c["features"]["recent_exposure"] for c in eligible_candidates])
        work_hours = np.array([c["working_hours_7d"] for c in eligible_candidates])

        efficiencies = compute_efficiency(distances, pressures)
        opp_credits = compute_opportunity_credit(exposures)
        median_hours = float(np.median(work_hours)) if len(work_hours) > 0 else 20.0
        workload_pressures = compute_workload_pressure(work_hours, median_hours)

        for i, c in enumerate(eligible_candidates):
            c["efficiency"] = round(float(efficiencies[i]), 4)
            c["opportunity_credit"] = round(float(opp_credits[i]), 4)
            c["workload_pressure"] = round(float(workload_pressures[i]), 4)

        duration_ms = (time.time() - start_time) * 1000

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role_description": self.role_description,
            "stage_number": self.stage_number,
            "status": "Completed",
            "duration_ms": round(duration_ms, 2),
            "input_summary": {
                "candidate_count": len(eligible_candidates),
                "configured_lambda": lambda_val
            },
            "output_summary": {
                "lambda_val": lambda_val,
                "mean_efficiency": round(float(np.mean(efficiencies)), 4),
                "mean_opportunity_credit": round(float(np.mean(opp_credits)), 4),
                "mean_workload_pressure": round(float(np.mean(workload_pressures)), 4),
                "median_work_hours": round(median_hours, 1)
            }
        }
