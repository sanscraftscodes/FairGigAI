import time
from typing import Dict, Any, List
from app.services.fairness_service import compute_wafr_score

class AllocationAgent:
    name = "Allocation Agent"
    agent_id = "agent_allocation"
    role_description = "Combines ML predicted success, operational efficiency, opportunity credit, and workload pressure using WAFR to select the optimal worker."
    stage_number = 5

    def run(
        self,
        eligible_candidates: List[Dict[str, Any]],
        lambda_val: float = 0.08,
        policy: str = "WAFR"
    ) -> Dict[str, Any]:
        start_time = time.time()

        if not eligible_candidates:
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "role_description": self.role_description,
                "stage_number": self.stage_number,
                "status": "Failed",
                "duration_ms": 0.0,
                "input_summary": {"eligible_candidates": 0},
                "output_summary": {"message": "No eligible candidates to allocate."},
                "selected_worker": None,
                "ranked_candidates": []
            }

        for c in eligible_candidates:
            p_succ = float(c.get("predicted_success", 0.0) or 0.0)
            eff = float(c.get("efficiency", 0.5) or 0.5)
            opp = float(c.get("opportunity_credit", 0.5) or 0.5)
            press = float(c.get("workload_pressure", 0.5) or 0.5)
            wafr = compute_wafr_score(p_succ, eff, opp, press, lambda_val)
            c["wafr_score"] = round(wafr, 4)

        # Apply ranking by policy
        if policy == "Nearest Eligible":
            eligible_candidates.sort(key=lambda x: (x["distance_km"], -x.get("predicted_success", 0.0)))
        elif policy == "ML-Only":
            eligible_candidates.sort(key=lambda x: (-x.get("predicted_success", 0.0), x["distance_km"]))
        else:  # WAFR default
            eligible_candidates.sort(key=lambda x: (-x["wafr_score"], -x.get("predicted_success", 0.0)))

        for rank_idx, c in enumerate(eligible_candidates, 1):
            c["rank"] = rank_idx

        selected = eligible_candidates[0] if eligible_candidates else None
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
                "policy": policy,
                "lambda_val": lambda_val
            },
            "output_summary": {
                "selected_worker_id": selected["worker_id"] if selected else None,
                "top_score": selected["wafr_score"] if selected else None,
                "top_predicted_success": selected.get("predicted_success") if selected else None,
                "policy_applied": policy
            },
            "selected_worker": selected,
            "ranked_candidates": eligible_candidates
        }
